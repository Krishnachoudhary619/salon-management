import time
import uuid
from uuid import UUID

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.common.responses import error_response
from app.core.config import Settings, get_settings
from app.core.constants import (
    DOCS_PATH_PREFIXES,
    LIVE_PROBE_PATHS,
    REQUEST_ID_HEADER,
    RETRY_AFTER_HEADER,
)
from app.core.rate_limit import SlidingWindowLimiter
from app.core.runtime import RuntimeState

logger = structlog.get_logger(__name__)

_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_DOCS_CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'"
)


def _settings(request: Request) -> Settings:
    stored = getattr(request.app.state, "settings", None)
    return stored if isinstance(stored, Settings) else get_settings()


def _runtime(request: Request) -> RuntimeState | None:
    runtime = getattr(request.app.state, "runtime", None)
    return runtime if isinstance(runtime, RuntimeState) else None


def _client_ip(request: Request, settings: Settings) -> str:
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", maxsplit=1)[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def _request_id(header_value: str | None) -> str:
    if header_value:
        try:
            return str(UUID(header_value))
        except ValueError:
            pass
    return str(uuid.uuid4())


def _error_body(message: str, status_code: int) -> JSONResponse:
    payload = error_response(message)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _is_docs_path(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in DOCS_PATH_PREFIXES)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and emit structured access logs without secrets."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = _settings(request)
        request_id = _request_id(request.headers.get(REQUEST_ID_HEADER))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            service=settings.APP_NAME,
            env=settings.APP_ENV,
        )

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        log = logger.debug if request.url.path in LIVE_PROBE_PATHS else logger.info
        log(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=_client_ip(request, settings),
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply browser isolation headers. CSP is relaxed only for Swagger/ReDoc."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        settings = _settings(request)
        docs = _is_docs_path(request.url.path)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()",
        )
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        response.headers.setdefault(
            "Content-Security-Policy",
            _DOCS_CSP if docs else _API_CSP,
        )
        if not docs:
            response.headers.setdefault("Cache-Control", "no-store")
        if settings.ENABLE_HSTS or settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response


class HostHeaderMiddleware(BaseHTTPMiddleware):
    """Reject unexpected Host headers with the standard error envelope."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = _settings(request)
        allowed = settings.allowed_host_list
        if "*" in allowed:
            return await call_next(request)
        host = (request.headers.get("host") or "").split(":", maxsplit=1)[0].lower()
        allowed_hosts = {item.lower() for item in allowed}
        if host not in allowed_hosts:
            logger.warning("rejected_host", host=host)
            return _error_body("Invalid host header", 400)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window. Auth routes use a stricter bucket."""

    def __init__(
        self,
        app: ASGIApp,
        limiter: SlidingWindowLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter or SlidingWindowLimiter()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = _settings(request)
        if not settings.RATE_LIMIT_ENABLED or request.url.path in LIVE_PROBE_PATHS:
            return await call_next(request)

        ip = _client_ip(request, settings)
        auth_limit = self._is_auth_sensitive(request, settings)
        if auth_limit:
            allowed, remaining, retry_after = self.limiter.hit(
                f"auth:{ip}",
                limit=settings.AUTH_RATE_LIMIT_REQUESTS,
                window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
            )
        else:
            allowed, remaining, retry_after = self.limiter.hit(
                f"ip:{ip}",
                limit=settings.RATE_LIMIT_REQUESTS,
                window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
            )
        if not allowed:
            logger.warning("rate_limited", client_ip=ip, path=request.url.path)
            limited = _error_body("Too many requests", 429)
            limited.headers[RETRY_AFTER_HEADER] = str(retry_after)
            limited.headers["X-RateLimit-Remaining"] = "0"
            return limited

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _is_auth_sensitive(self, request: Request, settings: Settings) -> bool:
        prefix = settings.API_V1_PREFIX.rstrip("/")
        return request.url.path in {f"{prefix}/auth/login", f"{prefix}/auth/refresh-token"}


class ShutdownDrainMiddleware(BaseHTTPMiddleware):
    """Refuse new traffic after SIGTERM while in-flight requests finish."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        runtime = _runtime(request)
        if runtime is None:
            return await call_next(request)
        if request.url.path == "/health":
            return await call_next(request)
        if runtime.shutting_down:
            response = _error_body("Service is shutting down", 503)
            response.headers[RETRY_AFTER_HEADER] = "0"
            return response
        accepted = await runtime.begin_request()
        if not accepted:
            response = _error_body("Service is shutting down", 503)
            response.headers[RETRY_AFTER_HEADER] = "0"
            return response
        try:
            return await call_next(request)
        finally:
            await runtime.end_request()
