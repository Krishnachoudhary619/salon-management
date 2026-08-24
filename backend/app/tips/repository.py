from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.common.repository import BaseRepository
from app.staff.models import Staff
from app.tips.models import Tip


class TipRepository(BaseRepository[Tip]):
    """Database access for discretionary staff tips."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Tip)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Tip]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(
                selectinload(Tip.staff).options(
                    noload(Staff.user),
                    noload(Staff.schedules),
                    noload(Staff.appointments),
                    noload(Staff.commissions),
                    noload(Staff.tips),
                    noload(Staff.tasks),
                ),
                noload(Tip.appointment),
            )
            .execution_options(populate_existing=True)
        )
