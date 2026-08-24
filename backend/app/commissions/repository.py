from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.commissions.models import Commission
from app.common.repository import BaseRepository
from app.staff.models import Staff


class CommissionRepository(BaseRepository[Commission]):
    """Database access for historical staff commissions."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Commission)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Commission]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(
                selectinload(Commission.staff).options(
                    noload(Staff.user),
                    noload(Staff.schedules),
                    noload(Staff.appointments),
                    noload(Staff.commissions),
                    noload(Staff.tips),
                    noload(Staff.tasks),
                ),
                noload(Commission.appointment),
            )
            .execution_options(populate_existing=True)
        )

    async def get_by_appointment_id(self, appointment_id: UUID) -> Commission | None:
        result = await self.session.execute(
            self._base_stmt().where(Commission.appointment_id == appointment_id)
        )
        return result.scalar_one_or_none()
