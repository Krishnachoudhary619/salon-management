from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.common.dependencies import PaginationDep
from app.common.enums import Permission, TaskStatus
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.tasks.dependencies import TaskServiceDep
from app.tasks.schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest

router = APIRouter(prefix="/tasks", tags=["Tasks"])

_READ = require_permissions(Permission.TASK_READ, Permission.TASK_READ_OWN, any_of=True)
_WRITE = require_permissions(Permission.TASK_WRITE, Permission.TASK_WRITE_OWN, any_of=True)
_ASSIGN = require_permissions(Permission.TASK_WRITE)


@router.get(
    "",
    summary="List tasks",
    description="Paginated staff chores. Staff callers only see tasks assigned to them.",
    response_model=APIResponse[PaginatedData[TaskResponse]],
)
async def list_tasks(
    pagination: PaginationDep,
    tasks: TaskServiceDep,
    actor: CurrentUser = Depends(_READ),
    assigned_staff_id: UUID | None = Query(default=None),
    task_status: TaskStatus | None = Query(default=None, alias="status"),
) -> APIResponse[PaginatedData[TaskResponse]]:
    page = await tasks.list_tasks(
        pagination,
        actor=actor,
        assigned_staff_id=assigned_staff_id,
        status=task_status,
    )
    return success_response(page)


@router.post(
    "",
    summary="Assign task",
    description="Create a PENDING task for a staff member. Admin only.",
    response_model=APIResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: TaskCreateRequest,
    tasks: TaskServiceDep,
    actor: CurrentUser = Depends(_ASSIGN),
) -> APIResponse[TaskResponse]:
    created = await tasks.create_task(payload, actor=actor)
    return success_response(created, message="Task assigned")


@router.get(
    "/{task_id}",
    summary="Get task",
    description="Retrieve a task. Staff callers may only read their own assignments.",
    response_model=APIResponse[TaskResponse],
)
async def get_task(
    task_id: UUID,
    tasks: TaskServiceDep,
    actor: CurrentUser = Depends(_READ),
) -> APIResponse[TaskResponse]:
    return success_response(await tasks.get_task(task_id, actor=actor))


@router.put(
    "/{task_id}",
    summary="Update task",
    description="Edit details or advance PENDING to IN_PROGRESS to COMPLETED. No reopen.",
    response_model=APIResponse[TaskResponse],
)
async def update_task(
    task_id: UUID,
    payload: TaskUpdateRequest,
    tasks: TaskServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[TaskResponse]:
    updated = await tasks.update_task(task_id, payload, actor=actor)
    return success_response(updated, message="Task updated")
