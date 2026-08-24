from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.common.repository import BaseRepository
from app.staff.models import Staff
from app.tasks.models import Task


class TaskRepository(BaseRepository[Task]):
    """Database access for staff work items."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Task]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(
                selectinload(Task.assigned_staff).options(
                    noload(Staff.user),
                    noload(Staff.schedules),
                    noload(Staff.appointments),
                    noload(Staff.commissions),
                    noload(Staff.tips),
                    noload(Staff.tasks),
                )
            )
            .execution_options(populate_existing=True)
        )
