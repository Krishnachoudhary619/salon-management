from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.responses import APIErrorResponse, ErrorItem
from app.core.config import get_settings
from app.core.constants import RETRY_AFTER_HEADER
from app.core.exceptions import AppException, RateLimitException
from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_items(errors: list[dict[str, Any]]) -> list[ErrorItem]:
    items: list[ErrorItem] = []
    for error in errors:
        items.append(
            ErrorItem(
                field=cast(str | None, error.get("field")),
                message=str(error.get("message", "Invalid value")),
            )
        )
    return items


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    payload = APIErrorResponse(
        success=False,
        message=exc.message,
        errors=_error_items(exc.errors),
    )
    headers: dict[str, str] = {}
    if isinstance(exc, RateLimitException):
        headers[RETRY_AFTER_HEADER] = str(exc.retry_after)
    return JSONResponse(
        status_code=exc.status_code,
        content=payload.model_dump(),
        headers=headers,
    )


async def request_validation_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors: list[ErrorItem] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        errors.append(
            ErrorItem(
                field=".".join(location) or None,
                message=str(error.get("msg", "Invalid value")),
            )
        )
    payload = APIErrorResponse(success=False, message="Validation error", errors=errors)
    return JSONResponse(status_code=422, content=payload.model_dump())


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request failed"
    payload = APIErrorResponse(success=False, message=message, errors=[])
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", error=str(exc))
    settings = get_settings()
    message = str(exc) if settings.DEBUG and not settings.is_production else "Internal server error"
    payload = APIErrorResponse(success=False, message=message, errors=[])
    return JSONResponse(status_code=500, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
