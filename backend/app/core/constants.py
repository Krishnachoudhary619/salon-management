from typing import Final

API_V1_PREFIX: Final[str] = "/api/v1"

DEFAULT_PAGE: Final[int] = 1
DEFAULT_LIMIT: Final[int] = 20
MAX_LIMIT: Final[int] = 100

ACCESS_TOKEN_TYPE: Final[str] = "access"
REFRESH_TOKEN_TYPE: Final[str] = "refresh"

SENSITIVE_LOG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "secret",
        "jwt",
        "jwt_secret",
        "credit_card",
        "card_number",
    }
)

REQUEST_ID_HEADER: Final[str] = "X-Request-ID"
RETRY_AFTER_HEADER: Final[str] = "Retry-After"

LIVE_PROBE_PATHS: Final[frozenset[str]] = frozenset({"/health", "/ready"})
DOCS_PATH_PREFIXES: Final[tuple[str, ...]] = ("/docs", "/redoc", "/openapi.json")
