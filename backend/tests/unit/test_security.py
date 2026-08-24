from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.common.enums import Role, TokenType
from app.core.config import Settings
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    hashed = hash_password("StrongPass123")
    assert hashed != "StrongPass123"
    assert verify_password("StrongPass123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_password_rejects_overlong_input() -> None:
    with pytest.raises(ValueError, match="72 bytes"):
        hash_password("x" * 80)


def test_access_token_round_trip() -> None:
    user_id = uuid4()
    token = create_access_token(
        subject=user_id,
        roles=[Role.ADMIN],
        email="admin@salon.test",
    )
    payload = decode_token(token, expected_type=TokenType.ACCESS)
    assert payload.sub == user_id
    assert payload.roles == [Role.ADMIN]
    assert payload.email == "admin@salon.test"
    assert payload.type == TokenType.ACCESS


def test_refresh_token_cannot_be_used_as_access() -> None:
    token = create_refresh_token(subject=uuid4(), roles=[Role.STAFF])
    with pytest.raises(UnauthorizedException, match="Invalid token type"):
        decode_token(token, expected_type=TokenType.ACCESS)


def test_expired_token_is_rejected() -> None:
    settings = Settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": TokenType.ACCESS.value,
            "roles": [Role.ADMIN.value],
            "email": None,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
            "jti": str(uuid4()),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedException, match="expired"):
        decode_token(token, expected_type=TokenType.ACCESS)


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(UnauthorizedException, match="Invalid token"):
        decode_token("not-a-jwt", expected_type=TokenType.ACCESS)
