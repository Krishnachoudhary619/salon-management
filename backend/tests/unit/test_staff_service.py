from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.enums import Role as RoleName
from app.common.enums import StaffStatus
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, NotFoundException, PermissionDeniedException
from app.core.security import CurrentUser
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.staff.repository import StaffRepository
from app.staff.schemas import StaffCreateRequest, StaffUpdateRequest
from app.staff.service import StaffService
from app.users.models import Role


@pytest.fixture
async def staff_session() -> AsyncGenerator[AsyncSession, None]:
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


def _create_payload(**overrides: object) -> StaffCreateRequest:
    data: dict[str, object] = {
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "password": "StaffPass123!",
        "phone": "9876500001",
        "designation": "Senior Stylist",
        "commission_percentage": Decimal("40.00"),
        "joining_date": date(2024, 1, 15),
    }
    data.update(overrides)
    return StaffCreateRequest.model_validate(data)


def _service(session: AsyncSession) -> StaffService:
    return StaffService(StaffRepository(session))


async def test_create_staff_links_user_and_role(staff_session: AsyncSession) -> None:
    created = await _service(staff_session).create_staff(_create_payload(), actor=_admin())
    assert created.name == "Priya Sharma"
    assert created.email == "priya@example.com"
    assert created.status == StaffStatus.ACTIVE
    assert created.commission_percentage == Decimal("40.00")
    assert created.user_id is not None


async def test_create_staff_rejects_duplicate_phone(staff_session: AsyncSession) -> None:
    service = _service(staff_session)
    actor = _admin()
    await service.create_staff(_create_payload(), actor=actor)
    with pytest.raises(ConflictException, match="phone"):
        await service.create_staff(
            _create_payload(email="other@example.com", phone="9876500001"),
            actor=actor,
        )


async def test_create_staff_rejects_duplicate_email(staff_session: AsyncSession) -> None:
    service = _service(staff_session)
    actor = _admin()
    await service.create_staff(_create_payload(), actor=actor)
    with pytest.raises(ConflictException, match="email"):
        await service.create_staff(
            _create_payload(email="priya@example.com", phone="9876500002"),
            actor=actor,
        )


async def test_update_and_list_staff(staff_session: AsyncSession) -> None:
    service = _service(staff_session)
    actor = _admin()
    created = await service.create_staff(_create_payload(), actor=actor)
    await service.create_staff(
        _create_payload(
            name="Rohan Mehta",
            email="rohan@example.com",
            phone="9876500002",
            designation="Barber",
        ),
        actor=actor,
    )
    updated = await service.update_staff(
        created.id,
        StaffUpdateRequest(designation="Lead Stylist", status=StaffStatus.ON_LEAVE),
        actor=actor,
    )
    assert updated.designation == "Lead Stylist"
    assert updated.status == StaffStatus.ON_LEAVE

    page = await service.list_staff(PaginationParams(page=1, limit=10, search="Priya"))
    assert page.total == 1
    assert page.items[0].id == created.id


async def test_deactivate_hides_staff_and_blocks_self(staff_session: AsyncSession) -> None:
    service = _service(staff_session)
    actor = _admin()
    created = await service.create_staff(_create_payload(), actor=actor)
    await service.deactivate_staff(created.id, actor=actor)
    with pytest.raises(NotFoundException):
        await service.get_staff(created.id)

    second = await service.create_staff(
        _create_payload(email="rohan@example.com", phone="9876500002"),
        actor=actor,
    )
    owner = CurrentUser(id=second.user_id, roles=[RoleName.ADMIN], email="rohan@example.com")
    with pytest.raises(PermissionDeniedException):
        await service.deactivate_staff(second.id, actor=owner)
