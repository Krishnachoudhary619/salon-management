from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.staff.repository import StaffRepository
from app.tasks.repository import TaskRepository
from app.tasks.service import TaskService


def get_task_service(session: SessionDep) -> TaskService:
    return TaskService(
        TaskRepository(session),
        staff_repository=StaffRepository(session),
    )


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
