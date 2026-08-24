from uuid import UUID

from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.common.repository import BaseRepository
from app.services.models import Service


class ServiceRepository(BaseRepository[Service]):
    """Database access for the salon service catalog."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Service)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Service]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(noload(Service.appointment_services))
        )

    async def get_by_name(self, name: str, *, exclude_id: UUID | None = None) -> Service | None:
        stmt = self._base_stmt().where(func.lower(Service.name) == name.lower())
        if exclude_id is not None:
            stmt = stmt.where(Service.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
