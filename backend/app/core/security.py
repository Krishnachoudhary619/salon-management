from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import bcrypt
import jwt
from pydantic import BaseModel, Field

from app.common.enums import Role, TokenType
from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedException


class TokenPayload(BaseModel):
    sub: UUID
    type: TokenType
    roles: list[Role] = Field(default_factory=list)
    email: str | None = None
    exp: datetime
    iat: datetime
    jti: UUID


class CurrentUser(BaseModel):
    """Authenticated identity extracted from a verified access token."""

    id: UUID
    roles: list[Role] = Field(default_factory=list)
    email: str | None = None

    @property
    def is_admin(self) -> bool:
        return Role.ADMIN in self.roles

    def has_role(self, *roles: Role) -> bool:
        return any(role in self.roles for role in roles)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def _encode_token(
    *,
    subject: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    roles: list[Role],
    email: str | None,
    settings: Settings,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type.value,
        "roles": [role.value for role in roles],
        "email": email,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    *,
    subject: UUID,
    roles: list[Role],
    email: str | None = None,
    settings: Settings | None = None,
) -> str:
    active_settings = settings or get_settings()
    return _encode_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=active_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        roles=roles,
        email=email,
        settings=active_settings,
    )


def create_refresh_token(
    *,
    subject: UUID,
    roles: list[Role],
    email: str | None = None,
    settings: Settings | None = None,
) -> str:
    active_settings = settings or get_settings()
    return _encode_token(
        subject=subject,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=active_settings.REFRESH_TOKEN_EXPIRE_DAYS),
        roles=roles,
        email=email,
        settings=active_settings,
    )


def decode_token(
    token: str,
    *,
    expected_type: TokenType,
    settings: Settings | None = None,
) -> TokenPayload:
    active_settings = settings or get_settings()
    try:
        raw_payload = jwt.decode(
            token,
            active_settings.JWT_SECRET,
            algorithms=[active_settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException("Invalid token") from exc

    payload = TokenPayload.model_validate(raw_payload)
    if payload.type != expected_type:
        raise UnauthorizedException("Invalid token type")
    return payload
