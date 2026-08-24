from collections.abc import AsyncGenerator
from datetime import date, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.appointments.dependencies import get_appointment_service
from app.appointments.schemas import (
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentUpdateRequest,
)
from app.appointments.service import AppointmentService
from app.common.enums import AppointmentStatus, StaffStatus
from app.common.enums import Role as RoleName
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, PermissionDeniedException, ValidationException
from app.core.security import CurrentUser
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreateRequest
from app.customers.service import CustomerService
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.schedules.repository import ScheduleRepository
from app.schedules.schemas import StaffScheduleCreateRequest
from app.schedules.service import ScheduleService
from app.services.repository import ServiceRepository
from app.services.schemas import ServiceCreateRequest
from app.services.service import ServiceService
from app.staff.repository import StaffRepository
from app.staff.schemas import StaffCreateRequest
from app.staff.service import StaffService
from app.users.models import Role


@pytest.fixture
async def booking_session() -> AsyncGenerator[AsyncSession, None]:
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


def _bookings(session: AsyncSession) -> AppointmentService:
    return get_appointment_service(session)


async def _seed(session: AsyncSession) -> tuple[UUID, UUID, UUID, UUID]:
    actor = _admin()
    staff = await StaffService(StaffRepository(session)).create_staff(
        StaffCreateRequest(
            name="Priya Sharma",
            email="priya@example.com",
            password="StaffPass123!",
            phone="9876500001",
            designation="Senior Stylist",
            commission_percentage=Decimal("40.00"),
            joining_date=date(2024, 1, 15),
            status=StaffStatus.ACTIVE,
        ),
        actor=actor,
    )
    await ScheduleService(ScheduleRepository(session)).create_schedule(
        StaffScheduleCreateRequest(
            staff_id=staff.id,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(18, 0),
        ),
        actor=actor,
    )
    hair = await ServiceService(ServiceRepository(session)).create_service(
        ServiceCreateRequest(
            name="Hair Cut",
            category="Hair",
            duration_minutes=30,
            price=Decimal("400.00"),
        ),
        actor=actor,
    )
    beard = await ServiceService(ServiceRepository(session)).create_service(
        ServiceCreateRequest(
            name="Beard Trim",
            category="Beard",
            duration_minutes=20,
            price=Decimal("250.00"),
        ),
        actor=actor,
    )
    customer = await CustomerService(CustomerRepository(session)).create_customer(
        CustomerCreateRequest(name="Meera Patel", phone="9876510001"),
        actor=actor,
    )
    return staff.id, customer.id, hair.id, beard.id


def _create(
    staff_id: UUID,
    customer_id: UUID,
    service_ids: list[UUID],
    *,
    start: str = "10:00:00",
    on_date: date = date(2026, 8, 24),
) -> AppointmentCreateRequest:
    return AppointmentCreateRequest(
        customer_id=customer_id,
        staff_id=staff_id,
        appointment_date=on_date,
        start_time=time.fromisoformat(start),
        service_ids=service_ids,
    )


async def test_create_calculates_duration_and_rejects_overlap(
    booking_session: AsyncSession,
) -> None:
    staff_id, customer_id, hair_id, beard_id = await _seed(booking_session)
    service = _bookings(booking_session)
    actor = _admin()
    created = await service.create_appointment(
        _create(staff_id, customer_id, [hair_id, beard_id]),
        actor=actor,
    )
    assert created.status == AppointmentStatus.PENDING
    assert created.duration_minutes == 50
    assert created.end_time == time(10, 50)
    assert len(created.services) == 2

    with pytest.raises(ConflictException, match="overlaps"):
        await service.create_appointment(
            _create(staff_id, customer_id, [hair_id], start="10:30:00"),
            actor=actor,
        )


async def test_status_workflow_and_cancel_rules(booking_session: AsyncSession) -> None:
    staff_id, customer_id, hair_id, _beard_id = await _seed(booking_session)
    service = _bookings(booking_session)
    actor = _admin()
    created = await service.create_appointment(
        _create(staff_id, customer_id, [hair_id]),
        actor=actor,
    )
    with pytest.raises(ValidationException, match="Cannot change status"):
        await service.change_status(created.id, AppointmentStatus.COMPLETED, actor=actor)

    confirmed = await service.change_status(created.id, AppointmentStatus.CONFIRMED, actor=actor)
    arrived = await service.change_status(confirmed.id, AppointmentStatus.ARRIVED, actor=actor)
    with pytest.raises(ValidationException, match="Cannot change status"):
        await service.cancel_appointment(arrived.id, actor=actor)

    in_progress = await service.change_status(
        arrived.id,
        AppointmentStatus.IN_PROGRESS,
        actor=actor,
    )
    completed = await service.change_status(
        in_progress.id,
        AppointmentStatus.COMPLETED,
        actor=actor,
    )
    assert completed.completed_at is not None
    with pytest.raises(ConflictException, match="rescheduled"):
        await service.reschedule_appointment(
            completed.id,
            AppointmentRescheduleRequest(
                appointment_date=date(2026, 8, 24),
                start_time=time(11, 0),
            ),
            actor=actor,
        )


async def test_reschedule_edit_list_and_calendar(booking_session: AsyncSession) -> None:
    staff_id, customer_id, hair_id, beard_id = await _seed(booking_session)
    service = _bookings(booking_session)
    actor = _admin()
    created = await service.create_appointment(
        _create(staff_id, customer_id, [hair_id]),
        actor=actor,
    )
    moved = await service.reschedule_appointment(
        created.id,
        AppointmentRescheduleRequest(
            appointment_date=date(2026, 8, 24),
            start_time=time(14, 0),
        ),
        actor=actor,
    )
    assert moved.start_time == time(14, 0)
    assert moved.end_time == time(14, 30)

    edited = await service.update_appointment(
        moved.id,
        AppointmentUpdateRequest(service_ids=[hair_id, beard_id], notes="Front desk note"),
        actor=actor,
    )
    assert edited.duration_minutes == 50
    assert edited.end_time == time(14, 50)
    assert edited.notes == "Front desk note"

    listed = await service.list_appointments(
        PaginationParams(page=1, limit=10),
        actor=actor,
        appointment_date=date(2026, 8, 24),
    )
    assert listed.total == 1
    calendar = await service.get_calendar(
        actor=actor,
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 25),
    )
    assert len(calendar.days) == 2
    assert len(calendar.days[0].appointments) == 1
    assert calendar.days[1].appointments == []

    cancelled = await service.cancel_appointment(edited.id, actor=actor)
    assert cancelled.status == AppointmentStatus.CANCELLED
    assert cancelled.cancelled_at is not None


async def test_staff_can_only_access_own_appointments(booking_session: AsyncSession) -> None:
    staff_id, customer_id, hair_id, _beard_id = await _seed(booking_session)
    service = _bookings(booking_session)
    created = await service.create_appointment(
        _create(staff_id, customer_id, [hair_id]),
        actor=_admin(),
    )
    other = CurrentUser(id=uuid4(), roles=[RoleName.STAFF], email="other@example.com")
    with pytest.raises(PermissionDeniedException):
        await service.get_appointment(created.id, actor=other)
