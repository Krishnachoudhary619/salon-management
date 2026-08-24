from collections.abc import AsyncGenerator
from datetime import date, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.appointments.engine import AvailabilityEngine
from app.appointments.models import Appointment
from app.common.enums import AppointmentStatus, StaffStatus
from app.common.enums import Role as RoleName
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import CurrentUser
from app.customers.models import Customer
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.schedules.repository import ScheduleRepository
from app.schedules.schemas import StaffScheduleCreateRequest
from app.schedules.service import ScheduleService
from app.staff.repository import StaffRepository
from app.staff.schemas import StaffCreateRequest
from app.staff.service import StaffService
from app.users.models import Role

MONDAY = date(2026, 8, 24)
TUESDAY = date(2026, 8, 25)


@pytest.fixture
async def engine_session() -> AsyncGenerator[AsyncSession, None]:
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


def _engine(session: AsyncSession) -> AvailabilityEngine:
    return AvailabilityEngine(ScheduleRepository(session))


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


async def _add_monday_hours(
    session: AsyncSession,
    staff_id: UUID,
    *,
    start: time = time(10, 0),
    end: time = time(13, 0),
) -> None:
    await ScheduleService(ScheduleRepository(session)).create_schedule(
        StaffScheduleCreateRequest(
            staff_id=staff_id,
            day_of_week=0,
            start_time=start,
            end_time=end,
        ),
        actor=_admin(),
    )


async def test_staff_must_exist(engine_session: AsyncSession) -> None:
    with pytest.raises(NotFoundException, match="Staff not found"):
        await _engine(engine_session).validate_slot(
            staff_id=uuid4(),
            on_date=MONDAY,
            start_time=time(10, 0),
            end_time=time(10, 30),
        )


async def test_staff_must_be_active(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session, status=StaffStatus.INACTIVE)
    await _add_monday_hours(engine_session, staff_id)
    with pytest.raises(ConflictException, match="Staff is not working"):
        await _engine(engine_session).validate_slot(
            staff_id=staff_id,
            on_date=MONDAY,
            start_time=time(10, 0),
            end_time=time(10, 30),
        )


async def test_staff_must_have_working_schedule_that_day(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    with pytest.raises(ConflictException, match="not working on this day"):
        await _engine(engine_session).validate_slot(
            staff_id=staff_id,
            on_date=TUESDAY,
            start_time=time(10, 0),
            end_time=time(10, 30),
        )


async def test_duration_must_fit_working_window(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id, start=time(10, 0), end=time(11, 0))
    with pytest.raises(ConflictException, match="duration does not fit"):
        await _engine(engine_session).validate_slot(
            staff_id=staff_id,
            on_date=MONDAY,
            start_time=time(10, 0),
            end_time=time(11, 30),
        )


async def test_overlap_is_rejected(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    customer = Customer(name="Meera Patel", phone="9876510001")
    engine_session.add(customer)
    await engine_session.flush()
    engine_session.add(
        Appointment(
            customer_id=customer.id,
            staff_id=staff_id,
            appointment_date=MONDAY,
            start_time=time(10, 30),
            end_time=time(11, 0),
            status=AppointmentStatus.CONFIRMED,
        )
    )
    await engine_session.flush()
    with pytest.raises(ConflictException, match="overlaps"):
        await _engine(engine_session).validate_slot(
            staff_id=staff_id,
            on_date=MONDAY,
            start_time=time(10, 0),
            end_time=time(10, 45),
        )


async def test_off_grid_slot_is_not_available(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    with pytest.raises(ConflictException, match="not available"):
        await _engine(engine_session).validate_slot(
            staff_id=staff_id,
            on_date=MONDAY,
            start_time=time(10, 7),
            end_time=time(10, 37),
        )


async def test_valid_slot_is_accepted(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    await _engine(engine_session).validate_slot(
        staff_id=staff_id,
        on_date=MONDAY,
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration_minutes=30,
    )


async def test_cancelled_appointment_does_not_block_slot(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    customer = Customer(name="Meera Patel", phone="9876510001")
    engine_session.add(customer)
    await engine_session.flush()
    engine_session.add(
        Appointment(
            customer_id=customer.id,
            staff_id=staff_id,
            appointment_date=MONDAY,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status=AppointmentStatus.CANCELLED,
        )
    )
    await engine_session.flush()
    await _engine(engine_session).validate_slot(
        staff_id=staff_id,
        on_date=MONDAY,
        start_time=time(10, 0),
        end_time=time(10, 30),
    )


async def test_reschedule_can_keep_the_same_slot(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    customer = Customer(name="Meera Patel", phone="9876510001")
    engine_session.add(customer)
    await engine_session.flush()
    booking = Appointment(
        customer_id=customer.id,
        staff_id=staff_id,
        appointment_date=MONDAY,
        start_time=time(10, 0),
        end_time=time(10, 30),
        status=AppointmentStatus.PENDING,
    )
    engine_session.add(booking)
    await engine_session.flush()
    await _engine(engine_session).validate_slot(
        staff_id=staff_id,
        on_date=MONDAY,
        start_time=time(10, 0),
        end_time=time(10, 30),
        exclude_appointment_id=booking.id,
    )


async def test_end_time_must_match_duration(engine_session: AsyncSession) -> None:
    staff_id = await _create_staff(engine_session)
    await _add_monday_hours(engine_session, staff_id)
    with pytest.raises(ValidationException, match="service duration"):
        await _engine(engine_session).validate_slot(
            staff_id=staff_id,
            on_date=MONDAY,
            start_time=time(10, 0),
            end_time=time(10, 30),
            duration_minutes=45,
        )
