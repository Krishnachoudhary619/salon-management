from uuid import UUID

from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.common.repository import BaseRepository
from app.customers.models import Customer


class CustomerRepository(BaseRepository[Customer]):
    """Database access for CRM customers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Customer)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Customer]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(noload(Customer.appointments))
        )

    async def get_by_phone(self, phone: str, *, exclude_id: UUID | None = None) -> Customer | None:
        stmt = self._base_stmt().where(Customer.phone == phone)
        if exclude_id is not None:
            stmt = stmt.where(Customer.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, *, exclude_id: UUID | None = None) -> Customer | None:
        stmt = self._base_stmt().where(func.lower(Customer.email) == email.lower())
        if exclude_id is not None:
            stmt = stmt.where(Customer.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
