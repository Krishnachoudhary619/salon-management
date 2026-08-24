from datetime import UTC, datetime
from uuid import UUID

from app.common.enums import Permission, SortOrder, TaskStatus
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from app.core.logging import get_logger
from app.core.permissions import has_permission
from app.core.security import CurrentUser
from app.staff.models import Staff
from app.staff.repository import StaffRepository
from app.tasks.models import Task
from app.tasks.repository import TaskRepository
from app.tasks.schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.tasks.workflow import as_status, can_transition

logger = get_logger(__name__)

_ALLOWED_SORT = {"created_at", "updated_at", "due_date", "status", "title"}


def to_task_response(task: Task) -> TaskResponse:
    staff_name = task.assigned_staff.name if task.assigned_staff is not None else ""
    return TaskResponse(
        id=task.id,
        assigned_staff_id=task.assigned_staff_id,
        assigned_staff_name=staff_name,
        title=task.title,
        description=task.description,
        status=as_status(task.status),
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


class TaskService(BaseService[Task]):
    """Staff chores with a one-way PENDING → IN_PROGRESS → COMPLETED workflow."""

    def __init__(
        self,
        repository: TaskRepository,
        *,
        staff_repository: StaffRepository,
    ) -> None:
        super().__init__(repository, resource_name="Task")
        self.task_repository = repository
        self.staff_repository = staff_repository

    async def create_task(self, payload: TaskCreateRequest, *, actor: CurrentUser) -> TaskResponse:
        staff = await self._require_staff(payload.assigned_staff_id)
        created = await self.task_repository.create(
            Task(
                assigned_staff_id=staff.id,
                title=payload.title,
                description=payload.description,
                status=TaskStatus.PENDING,
                due_date=payload.due_date,
            ),
            created_by=actor.id,
        )
        logger.info("task_created", task_id=str(created.id), staff_id=str(staff.id))
        loaded = await self.task_repository.get_by_id(created.id)
        assert loaded is not None
        return to_task_response(loaded)

    async def get_task(self, task_id: UUID, *, actor: CurrentUser) -> TaskResponse:
        task = await self.get(task_id)
        await self._ensure_can_access(task, actor, write=False)
        return to_task_response(task)

    async def list_tasks(
        self,
        params: PaginationParams,
        *,
        actor: CurrentUser,
        assigned_staff_id: UUID | None = None,
        status: TaskStatus | None = None,
    ) -> PaginatedData[TaskResponse]:
        scoped_staff_id = await self._scoped_staff_id(actor, assigned_staff_id, write=False)
        if params.sort_by is None:
            params.sort_by = "created_at"
            params.sort_order = SortOrder.DESC
        filters = []
        if scoped_staff_id is not None:
            filters.append(Task.assigned_staff_id == scoped_staff_id)
        if status is not None:
            filters.append(Task.status == status)
        page = await self.task_repository.list(
            params,
            filters=filters or None,
            search_fields=["title", "description"],
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_task_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def update_task(
        self,
        task_id: UUID,
        payload: TaskUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> TaskResponse:
        task = await self.get(task_id)
        await self._ensure_can_access(task, actor, write=True)
        changes = payload.model_dump(exclude_unset=True)
        if "assigned_staff_id" in changes:
            if not has_permission(actor, Permission.TASK_WRITE):
                raise PermissionDeniedException("You cannot reassign this task")
            staff = await self._require_staff(changes["assigned_staff_id"])
            task.assigned_staff_id = staff.id
        if "title" in changes:
            task.title = changes["title"]
        if "description" in changes:
            task.description = changes["description"]
        if "due_date" in changes:
            task.due_date = changes["due_date"]
        if "status" in changes:
            await self._apply_status(task, as_status(changes["status"]))
        await self.task_repository.update(task, updated_by=actor.id)
        loaded = await self.task_repository.get_by_id(task.id)
        assert loaded is not None
        logger.info("task_updated", task_id=str(task.id), status=str(loaded.status))
        return to_task_response(loaded)

    async def _apply_status(self, task: Task, target: TaskStatus) -> None:
        current = as_status(task.status)
        if target == current:
            return
        if current == TaskStatus.COMPLETED:
            raise ValidationException("Completed tasks cannot be reopened")
        if not can_transition(current, target):
            raise ValidationException(
                f"Cannot change status from {current.value} to {target.value}"
            )
        task.status = target
        if target == TaskStatus.COMPLETED:
            task.completed_at = datetime.now(UTC)

    async def _require_staff(self, staff_id: UUID) -> Staff:
        staff = await self.staff_repository.get_by_id(staff_id)
        if staff is None:
            raise NotFoundException("Staff not found")
        return staff

    async def _scoped_staff_id(
        self,
        actor: CurrentUser,
        requested_staff_id: UUID | None,
        *,
        write: bool,
    ) -> UUID | None:
        full = Permission.TASK_WRITE if write else Permission.TASK_READ
        if has_permission(actor, full):
            return requested_staff_id
        profile = await self.staff_repository.get_by_user_id(actor.id)
        if profile is None:
            raise PermissionDeniedException("No staff profile is linked to this account")
        if requested_staff_id is not None and requested_staff_id != profile.id:
            raise PermissionDeniedException("You can only access your own tasks")
        return profile.id

    async def _ensure_can_access(self, task: Task, actor: CurrentUser, *, write: bool) -> None:
        scoped = await self._scoped_staff_id(actor, None, write=write)
        if scoped is not None and task.assigned_staff_id != scoped:
            raise PermissionDeniedException("You can only access your own tasks")
