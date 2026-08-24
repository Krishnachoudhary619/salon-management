from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.common.enums import StaffStatus, TaskStatus
from app.common.pagination import PaginationParams
from app.core.exceptions import PermissionDeniedException, ValidationException
from app.core.security import CurrentUser
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.staff.repository import StaffRepository
from app.staff.schemas import StaffCreateRequest
from app.staff.service import StaffService
from app.tasks.dependencies import get_task_service
from app.tasks.schemas import TaskCreateRequest, TaskUpdateRequest
from app.tasks.service import TaskService
from app.users.models import Role


@pytest.fixture
async def task_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        for name in RoleName:
            session.add(Role(name=name))
        await session.flush()
        yield session
    await engine.dispose()


def _admin() -> CurrentUser:
    return CurrentUser(id=uuid4(), roles=[RoleName.ADMIN], email="admin@example.com")


def _tasks(session: AsyncSession) -> TaskService:
    return get_task_service(session)


async def _staff(session: AsyncSession, *, email: str = "priya@example.com") -> UUID:
    created = await StaffService(StaffRepository(session)).create_staff(
        StaffCreateRequest(
            name="Priya Sharma" if "priya" in email else "Rohan Mehta",
            email=email,
            password="StaffPass123!",
            phone="9876500001" if "priya" in email else "9876500002",
            designation="Senior Stylist",
            commission_percentage=Decimal("40.00"),
            joining_date=date(2024, 1, 15),
            status=StaffStatus.ACTIVE,
        ),
        actor=_admin(),
    )
    return created.id


async def test_admin_assigns_and_staff_advances_status(task_session: AsyncSession) -> None:
    staff_id = await _staff(task_session)
    tasks = _tasks(task_session)
    actor = _admin()
    created = await tasks.create_task(
        TaskCreateRequest(
            assigned_staff_id=staff_id,
            title="Restock shampoo",
            description="Front shelf",
            due_date=date(2026, 8, 25),
        ),
        actor=actor,
    )
    assert created.status == TaskStatus.PENDING
    assert created.completed_at is None
    assert created.assigned_staff_name == "Priya Sharma"

    with pytest.raises(ValidationException, match="Cannot change status"):
        await tasks.update_task(
            created.id,
            TaskUpdateRequest(status=TaskStatus.COMPLETED),
            actor=actor,
        )

    started = await tasks.update_task(
        created.id,
        TaskUpdateRequest(status=TaskStatus.IN_PROGRESS),
        actor=actor,
    )
    assert started.status == TaskStatus.IN_PROGRESS
    done = await tasks.update_task(
        created.id,
        TaskUpdateRequest(status=TaskStatus.COMPLETED),
        actor=actor,
    )
    assert done.status == TaskStatus.COMPLETED
    assert done.completed_at is not None

    with pytest.raises(ValidationException, match="cannot be reopened"):
        await tasks.update_task(
            created.id,
            TaskUpdateRequest(status=TaskStatus.PENDING),
            actor=actor,
        )

    listed = await tasks.list_tasks(
        PaginationParams(page=1, limit=10),
        actor=actor,
        status=TaskStatus.COMPLETED,
    )
    assert listed.total == 1


async def test_staff_can_update_own_task_but_not_others(task_session: AsyncSession) -> None:
    staff_id = await _staff(task_session)
    other_id = await _staff(task_session, email="rohan@example.com")
    tasks = _tasks(task_session)
    admin = _admin()
    own_task = await tasks.create_task(
        TaskCreateRequest(assigned_staff_id=staff_id, title="Clean stations"),
        actor=admin,
    )
    other_task = await tasks.create_task(
        TaskCreateRequest(assigned_staff_id=other_id, title="Laundry"),
        actor=admin,
    )
    profile = await StaffRepository(task_session).get_by_id(staff_id)
    assert profile is not None
    owner = CurrentUser(id=profile.user_id, roles=[RoleName.STAFF], email="priya@example.com")

    listed = await tasks.list_tasks(PaginationParams(page=1, limit=10), actor=owner)
    assert listed.total == 1
    assert listed.items[0].id == own_task.id

    started = await tasks.update_task(
        own_task.id,
        TaskUpdateRequest(status=TaskStatus.IN_PROGRESS),
        actor=owner,
    )
    assert started.status == TaskStatus.IN_PROGRESS

    with pytest.raises(PermissionDeniedException, match="own tasks"):
        await tasks.get_task(other_task.id, actor=owner)
    with pytest.raises(PermissionDeniedException, match="reassign"):
        await tasks.update_task(
            own_task.id,
            TaskUpdateRequest(assigned_staff_id=other_id),
            actor=owner,
        )


async def test_receptionist_cannot_list_tasks(task_session: AsyncSession) -> None:
    desk = CurrentUser(id=uuid4(), roles=[RoleName.RECEPTIONIST], email="desk@example.com")
    with pytest.raises(PermissionDeniedException):
        await _tasks(task_session).list_tasks(PaginationParams(page=1, limit=10), actor=desk)
