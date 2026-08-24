import pytest
from pydantic import ValidationError

from app.core.config import Settings

_PROD_SECRET = "production-jwt-secret-key-must-be-unique-32"


def test_database_url_uses_asyncpg() -> None:
    settings = Settings(
        DB_USER="salon",
        DB_PASSWORD="secret",
        DB_HOST="db",
        DB_PORT=5432,
        DB_NAME="salon",
    )
    assert settings.database_url == "postgresql+asyncpg://salon:secret@db:5432/salon"


def test_database_url_encodes_password() -> None:
    settings = Settings(
        DB_USER="salon",
        DB_PASSWORD="p@ss:w/ord",
        DB_HOST="db",
        DB_NAME="salon",
    )
    assert "p%40ss%3Aw%2Ford" in settings.database_url


def test_cors_origin_parsing() -> None:
    settings = Settings(CORS_ORIGINS="http://localhost:3000, https://salon.example")
    assert settings.cors_origin_list == ["http://localhost:3000", "https://salon.example"]


def test_production_rejects_weak_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", JWT_SECRET="local-dev-only-secret-key-not-for-prod")


def test_production_requires_explicit_cors_and_hosts() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(
            APP_ENV="production",
            JWT_SECRET=_PROD_SECRET,
            CORS_ORIGINS="*",
            ALLOWED_HOSTS="api.example.com",
            DEBUG=False,
        )
    with pytest.raises(ValidationError, match="ALLOWED_HOSTS"):
        Settings(
            APP_ENV="production",
            JWT_SECRET=_PROD_SECRET,
            CORS_ORIGINS="https://app.example.com",
            ALLOWED_HOSTS="*",
            DEBUG=False,
        )
    with pytest.raises(ValidationError, match="DEBUG"):
        Settings(
            APP_ENV="production",
            JWT_SECRET=_PROD_SECRET,
            CORS_ORIGINS="https://app.example.com",
            ALLOWED_HOSTS="api.example.com",
            DEBUG=True,
        )


def test_production_accepts_hardened_settings() -> None:
    settings = Settings(
        APP_ENV="production",
        JWT_SECRET=_PROD_SECRET,
        CORS_ORIGINS="https://app.example.com",
        ALLOWED_HOSTS="api.example.com",
        DEBUG=False,
    )
    assert settings.docs_enabled is False
    assert settings.is_production is True
