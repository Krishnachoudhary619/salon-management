from functools import lru_cache
from typing import Any, Literal, Self
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ASYNCPG_UNSUPPORTED_QUERY_KEYS = frozenset(
    {"sslmode", "channel_binding", "sslrootcert", "sslcert", "sslkey"}
)


def to_asyncpg_database_url(raw: str) -> str:
    """Normalize a hosted or local Postgres URL for SQLAlchemy + asyncpg."""
    url = raw.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parsed = urlparse(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in _ASYNCPG_UNSUPPORTED_QUERY_KEYS
    ]
    return urlunparse(parsed._replace(query=urlencode(query)))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = "Salon Backend"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Prefer DATABASE_URL on hosted Postgres (Neon, Render, Supabase).
    DATABASE_URL: str | None = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "salon"
    DB_USER: str = "salon"
    DB_PASSWORD: str = "salon"
    DB_SSL: bool | None = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_POOL_TIMEOUT_SECONDS: int = 30
    DB_CONNECT_TIMEOUT_SECONDS: float = 5.0
    DB_COMMAND_TIMEOUT_SECONDS: float = 10.0
    DB_CONNECT_ATTEMPTS: int = 30
    DB_CONNECT_RETRY_BASE_SECONDS: float = 0.5
    DB_CONNECT_RETRY_MAX_SECONDS: float = 5.0

    JWT_SECRET: str = Field(default="local-dev-only-secret-key-not-for-prod", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ORIGINS: str = "*"
    ALLOWED_HOSTS: str = "*"
    TRUST_PROXY_HEADERS: bool = False
    ENABLE_HSTS: bool = False

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    AUTH_RATE_LIMIT_REQUESTS: int = 10
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60

    WAIT_FOR_DATABASE: bool = True
    READY_CHECK_DATABASE: bool = True
    GRACEFUL_SHUTDOWN_SECONDS: float = 30.0

    SEED_ADMIN_NAME: str = "Salon Admin"
    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "AdminPass123!"
    SEED_STAFF_PASSWORD: str = "StaffPass123!"

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        weak_secret = (
            self.JWT_SECRET.startswith("change-me")
            or self.JWT_SECRET.startswith("local-dev")
            or "not-for-prod" in self.JWT_SECRET
        )
        if not self.is_production:
            return self
        if weak_secret:
            raise ValueError("JWT_SECRET must be a unique secret in production")
        if self.cors_origin_list == ["*"]:
            raise ValueError("CORS_ORIGINS must be an explicit allowlist in production")
        if self.allowed_host_list == ["*"]:
            raise ValueError("ALLOWED_HOSTS must be an explicit allowlist in production")
        if self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        return self

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return to_asyncpg_database_url(self.DATABASE_URL)
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_ssl(self) -> bool:
        if self.DB_SSL is not None:
            return self.DB_SSL
        return bool(self.DATABASE_URL)

    @property
    def database_uses_pooler(self) -> bool:
        raw = self.DATABASE_URL or ""
        host = (urlparse(raw).hostname or "").lower()
        return "-pooler." in host or ".pooler." in host

    @property
    def asyncpg_connect_args(self) -> dict[str, Any]:
        args: dict[str, Any] = {
            "timeout": self.DB_CONNECT_TIMEOUT_SECONDS,
            "command_timeout": self.DB_COMMAND_TIMEOUT_SECONDS,
        }
        if self.database_ssl:
            args["ssl"] = True
        if self.database_uses_pooler:
            args["statement_cache_size"] = 0
        return args

    @property
    def cors_origin_list(self) -> list[str]:
        return _csv_list(self.CORS_ORIGINS)

    @property
    def allowed_host_list(self) -> list[str]:
        return _csv_list(self.ALLOWED_HOSTS)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production


def _csv_list(raw: str) -> list[str]:
    if raw.strip() == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
