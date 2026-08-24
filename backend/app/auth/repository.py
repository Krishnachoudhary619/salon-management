from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import RefreshToken
from app.common.repository import BaseRepository
from app.users.models import User, UserRole


class AuthRepository(BaseRepository[RefreshToken]):
    """Database access for login identities and persisted refresh tokens."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RefreshToken)

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(func.lower(User.email) == email.lower(), User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id, User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_refresh_token_by_jti(self, jti: UUID) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
                RefreshToken.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_active_refresh_tokens(self, user_id: UUID) -> list[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.is_deleted.is_(False),
            )
        )
        return list(result.scalars().all())

    async def revoke_token(
        self,
        token: RefreshToken,
        *,
        replaced_by_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> RefreshToken:
        token.revoked_at = datetime.now(UTC)
        token.replaced_by_id = replaced_by_id
        return await self.update(token, updated_by=actor_id)

    async def revoke_user_tokens(self, user_id: UUID, *, actor_id: UUID | None = None) -> int:
        tokens = await self.list_active_refresh_tokens(user_id)
        for token in tokens:
            await self.revoke_token(token, actor_id=actor_id)
        return len(tokens)
