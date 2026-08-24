from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.common.enums import Role as RoleName
from app.common.repository import BaseRepository
from app.staff.models import Staff
from app.users.models import Role, User, UserRole


class StaffRepository(BaseRepository[Staff]):
    """Database access for staff profiles and their login users."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Staff)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Staff]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(
                selectinload(Staff.user).options(
                    noload(User.refresh_tokens),
                    noload(User.user_roles),
                    noload(User.staff),
                ),
                noload(Staff.appointments),
                noload(Staff.schedules),
                noload(Staff.commissions),
                noload(Staff.tips),
                noload(Staff.tasks),
            )
        )

    async def get_by_phone(self, phone: str, *, exclude_id: UUID | None = None) -> Staff | None:
        stmt = self._base_stmt().where(Staff.phone == phone)
        if exclude_id is not None:
            stmt = stmt.where(Staff.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Staff | None:
        result = await self.session.execute(self._base_stmt().where(Staff.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower(), User.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: RoleName) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name, Role.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def assign_role(self, user_id: UUID, role_id: UUID, *, actor_id: UUID | None) -> None:
        assignment = UserRole(user_id=user_id, role_id=role_id)
        if actor_id is not None:
            assignment.created_by = actor_id
            assignment.updated_by = actor_id
        self.session.add(assignment)
        await self.session.flush()
