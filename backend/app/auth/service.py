import hashlib
from datetime import UTC, datetime
from uuid import UUID

from app.auth.models import RefreshToken
from app.auth.repository import AuthRepository
from app.auth.schemas import AuthUserResponse, LoginRequest, TokenResponse
from app.common.enums import Role, TokenType
from app.core.exceptions import UnauthorizedException
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.users.models import User

logger = get_logger(__name__)

_INVALID_CREDENTIALS = "Invalid email or password"


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def extract_roles(user: User) -> list[Role]:
    roles: list[Role] = []
    for assignment in user.user_roles:
        if assignment.is_deleted:
            continue
        roles.append(Role(assignment.role.name))
    return roles


def to_auth_user(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        roles=extract_roles(user),
    )


class AuthService:
    """Authentication use cases: login, logout, refresh, and current user."""

    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.repository.get_user_by_email(str(payload.email))
        if user is None or not verify_password(payload.password, user.password_hash):
            logger.info("login_failed", email=str(payload.email))
            raise UnauthorizedException(_INVALID_CREDENTIALS)
        if not user.is_active:
            logger.info("login_disabled", user_id=str(user.id))
            raise UnauthorizedException("Account is disabled")
        tokens = await self._issue_tokens(user)
        logger.info("user_logged_in", user_id=str(user.id), email=user.email)
        return tokens

    async def logout(self, user_id: UUID) -> None:
        revoked = await self.repository.revoke_user_tokens(user_id, actor_id=user_id)
        logger.info("user_logged_out", user_id=str(user_id), revoked=revoked)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        stored = await self.repository.get_refresh_token_by_jti(payload.jti)
        if stored is None:
            raise UnauthorizedException("Invalid refresh token")
        if stored.revoked_at is not None:
            await self.repository.revoke_user_tokens(stored.user_id, actor_id=stored.user_id)
            logger.info("refresh_token_reuse_detected", user_id=str(stored.user_id))
            raise UnauthorizedException("Refresh token has already been used")
        if self._aware(stored.expires_at) <= datetime.now(UTC):
            await self.repository.revoke_token(stored, actor_id=stored.user_id)
            raise UnauthorizedException("Refresh token has expired")
        if stored.token_hash != hash_refresh_token(refresh_token):
            raise UnauthorizedException("Invalid refresh token")
        if stored.user_id != payload.sub:
            raise UnauthorizedException("Invalid refresh token")

        user = await self.repository.get_user_by_id(stored.user_id)
        if user is None or not user.is_active:
            await self.repository.revoke_user_tokens(stored.user_id, actor_id=stored.user_id)
            raise UnauthorizedException("Account is disabled")

        tokens = await self._issue_tokens(user, replacing=stored)
        logger.info("refresh_token_rotated", user_id=str(user.id))
        return tokens

    async def get_me(self, user_id: UUID) -> AuthUserResponse:
        user = await self.repository.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("Authentication required")
        return to_auth_user(user)

    async def _issue_tokens(
        self,
        user: User,
        *,
        replacing: RefreshToken | None = None,
    ) -> TokenResponse:
        roles = extract_roles(user)
        access_token = create_access_token(subject=user.id, roles=roles, email=user.email)
        refresh_token = create_refresh_token(subject=user.id, roles=roles, email=user.email)
        refresh_payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        stored = await self.repository.create(
            RefreshToken(
                user_id=user.id,
                jti=refresh_payload.jti,
                token_hash=hash_refresh_token(refresh_token),
                expires_at=self._aware(refresh_payload.exp),
            ),
            created_by=user.id,
        )
        if replacing is not None:
            await self.repository.revoke_token(
                replacing,
                replaced_by_id=stored.id,
                actor_id=user.id,
            )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=to_auth_user(user),
        )

    @staticmethod
    def _aware(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
