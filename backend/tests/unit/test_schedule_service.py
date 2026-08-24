from collections.abc import AsyncGenerator
from datetime import date, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.appointments.models import Appointment
from app.common.enums import AppointmentStatus, StaffStatus
from app.common.enums import Role as RoleName
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import CurrentUser
from app.customers.models import Customer
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.schedules.repository import ScheduleRepository
from app.schedules.schemas import (
    StaffScheduleCreateRequest,
    StaffScheduleUpdateRequest,
    WeeklyScheduleReplaceRequest,
    WeeklyWindowRequest,
)
from app.schedules.service import ScheduleService
from app.staff.repository import StaffRepository
from app.staff.schemas import StaffCreateRequest
from app.staff.service import StaffService
from app.users.models import Role


@pytest.fixture
async def schedule_session() -> AsyncGenerator[AsyncSession, None]:
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


def _schedules(session: AsyncSession) -> ScheduleService:
    return ScheduleService(ScheduleRepository(session))


async def _create_staff(
    session: AsyncSession,
    *,
    email: str = "priya@example.com",
    phone: str = "9876500001",
    status: StaffStatus = StaffStatus.ACTIVE,
) -> UUID:
    created = await StaffService(StaffRepository(session)).create_staff(
        StaffCreateRequest(
            name="Priya Sharma",
            email=email,
            password="StaffPass123!",
            phone=phone,
            designation="Senior Stylist",
            commission_percentage=Decimal("40.00"),
            joining_date=date(2024, 1, 15),
            status=status,
        ),
        actor=_admin(),
    )
    return created.id


def _window(
    staff_id: UUID,
    *,
    day_of_week: int = 0,
    start: str = "10:00:00",
    end: str = "13:00:00",
) -> StaffScheduleCreateRequest:
    return StaffScheduleCreateRequest(
        staff_id=staff_id,
        day_of_week=day_of_week,
        start_time=time.fromisoformat(start),
        end_time=time.fromisoformat(end),
    )


async def test_create_split_day_and_reject_overlap(schedule_session: AsyncSession) -> None:
    staff_id = await _create_staff(schedule_session)
    service = _schedules(schedule_session)
    actor = _admin()
    morning = await service.create_schedule(_window(staff_id), actor=actor)
    afternoon = await service.create_schedule(
        _window(staff_id, start="15:00:00", end="19:00:00"),
        actor=actor,
    )
    assert morning.id != afternoon.id

    with pytest.raises(ConflictException, match="overlap"):
        await service.create_schedule(
            _window(staff_id, start="12:00:00", end="16:00:00"),
            actor=actor,
        )

    adjacent = await service.create_schedule(
        _window(staff_id, start="13:00:00", end="15:00:00"),
        actor=actor,
    )
    assert adjacent.start_time == time(13, 0)


async def test_weekly_replace_and_list(schedule_session: AsyncSession) -> None:
    staff_id = await _create_staff(schedule_session)
    service = _schedules(schedule_session)
    actor = _admin()
    await service.create_schedule(_window(staff_id), actor=actor)
    replaced = await service.replace_weekly_schedule(
        staff_id,
        WeeklyScheduleReplaceRequest(
            windows=[
                WeeklyWindowRequest(
                    day_of_week=0,
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                ),
                WeeklyWindowRequest(
                    day_of_week=2,
                    start_time=time(10, 0),
                    end_time=time(14, 0),
                ),
            ]
        ),
        actor=actor,
    )
    assert len(replaced.windows) == 2
    page = await service.list_schedules(PaginationParams(page=1, limit=10), staff_id=staff_id)
    assert page.total == 2


async def test_availability_skips_busy_and_inactive_staff(schedule_session: AsyncSession) -> None:
    staff_id = await _create_staff(schedule_session)
    service = _schedules(schedule_session)
    actor = _admin()
    await service.create_schedule(
        _window(staff_id, start="10:00:00", end="12:00:00"),
        actor=actor,
    )
    monday = date(2026, 8, 24)
    open_slots = await service.get_availability(
        staff_id=staff_id,
        on_date=monday,
        duration_minutes=30,
    )
    assert open_slots.slots[0].start_time == time(10, 0)
    assert any(slot.start_time == time(10, 30) for slot in open_slots.slots)

    customer = Customer(name="Meera Patel", phone="9876510001")
    schedule_session.add(customer)
    await schedule_session.flush()
    schedule_session.add(
        Appointment(
            customer_id=customer.id,
            staff_id=staff_id,
            appointment_date=monday,
            start_time=time(10, 30),
            end_time=time(11, 0),
            status=AppointmentStatus.CONFIRMED,
        )
    )
    await schedule_session.flush()

    after = await service.get_availability(
        staff_id=staff_id,
        on_date=monday,
        duration_minutes=30,
    )
    starts = [slot.start_time for slot in after.slots]
    assert time(10, 30) not in starts
    assert time(10, 0) in starts

    await service.assert_slot_available(
        staff_id=staff_id,
        on_date=monday,
        start_time=time(11, 0),
        end_time=time(11, 30),
    )
    with pytest.raises(ConflictException, match="overlaps"):
        await service.assert_slot_available(
            staff_id=staff_id,
            on_date=monday,
            start_time=time(10, 30),
            end_time=time(11, 0),
        )

    inactive_id = await _create_staff(
        schedule_session,
        email="rohan@example.com",
        phone="9876500002",
        status=StaffStatus.INACTIVE,
    )
    with pytest.raises(ConflictException, match="not working"):
        await service.get_availability(
            staff_id=inactive_id,
            on_date=monday,
            duration_minutes=30,
        )


async def test_update_delete_and_missing_staff(schedule_session: AsyncSession) -> None:
    staff_id = await _create_staff(schedule_session)
    service = _schedules(schedule_session)
    actor = _admin()
    created = await service.create_schedule(_window(staff_id), actor=actor)
    updated = await service.update_schedule(
        created.id,
        StaffScheduleUpdateRequest(end_time=time(14, 0)),
        actor=actor,
    )
    assert updated.end_time == time(14, 0)

    await service.delete_schedule(created.id, actor=actor)
    with pytest.raises(NotFoundException):
        await service.get_schedule(created.id)

    with pytest.raises(NotFoundException):
        await service.create_schedule(_window(uuid4()), actor=actor)

    with pytest.raises(ValidationException, match="duration_minutes"):
        await service.get_availability(staff_id=staff_id, on_date=date(2026, 8, 24))
