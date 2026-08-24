from collections.abc import AsyncGenerator
from datetime import date, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.appointments.dependencies import get_appointment_service
from app.appointments.schemas import AppointmentCreateRequest
from app.appointments.service import AppointmentService
from app.billing.dependencies import get_billing_service
from app.billing.schemas import PaymentCreateRequest
from app.commissions.dependencies import get_commission_service
from app.common.enums import AppointmentStatus, PaymentMethod, StaffStatus
from app.common.enums import Role as RoleName
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, PermissionDeniedException
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
from app.tips.dependencies import get_tip_service
from app.tips.schemas import TipCreateRequest, TipUpdateRequest
from app.tips.service import TipService
from app.users.models import Role

_WORKFLOW = (
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.ARRIVED,
    AppointmentStatus.IN_PROGRESS,
    AppointmentStatus.COMPLETED,
)


@pytest.fixture
async def tip_session() -> AsyncGenerator[AsyncSession, None]:
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


def _tips(session: AsyncSession) -> TipService:
    return get_tip_service(session)


async def _seed(session: AsyncSession) -> tuple[UUID, UUID, UUID]:
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
    customer = await CustomerService(CustomerRepository(session)).create_customer(
        CustomerCreateRequest(name="Meera Patel", phone="9876510001"),
        actor=actor,
    )
    return staff.id, customer.id, hair.id


async def _book(session: AsyncSession) -> tuple[UUID, UUID]:
    staff_id, customer_id, hair_id = await _seed(session)
    created = await _bookings(session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=date(2026, 8, 24),
            start_time=time(10, 0),
            service_ids=[hair_id],
        ),
        actor=_admin(),
    )
    return created.id, staff_id


async def test_add_edit_and_list_tips(tip_session: AsyncSession) -> None:
    appointment_id, staff_id = await _book(tip_session)
    tips = _tips(tip_session)
    actor = _admin()
    first = await tips.create_tip(
        TipCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("100.00"),
            notes="Cash tip",
        ),
        actor=actor,
    )
    assert first.staff_id == staff_id
    assert first.staff_name == "Priya Sharma"
    assert first.amount == Decimal("100.00")
    assert first.notes == "Cash tip"

    second = await tips.create_tip(
        TipCreateRequest(appointment_id=appointment_id, amount=Decimal("50.00")),
        actor=actor,
    )
    assert second.id != first.id

    edited = await tips.update_tip(
        first.id,
        TipUpdateRequest(amount=Decimal("120.00"), notes="Adjusted"),
        actor=actor,
    )
    assert edited.amount == Decimal("120.00")
    assert edited.notes == "Adjusted"

    listed = await tips.list_tips(
        PaginationParams(page=1, limit=10),
        actor=actor,
        appointment_id=appointment_id,
    )
    assert listed.total == 2
    by_staff = await tips.list_staff_tips(
        staff_id,
        PaginationParams(page=1, limit=10),
        actor=actor,
    )
    assert by_staff.total == 2
    loaded = await tips.get_tip(first.id, actor=actor)
    assert loaded.amount == Decimal("120.00")


async def test_tip_rejected_on_cancelled_appointment(tip_session: AsyncSession) -> None:
    appointment_id, _staff_id = await _book(tip_session)
    actor = _admin()
    await _bookings(tip_session).cancel_appointment(appointment_id, actor=actor)
    with pytest.raises(ConflictException, match="cancelled or no-show"):
        await _tips(tip_session).create_tip(
            TipCreateRequest(appointment_id=appointment_id, amount=Decimal("50.00")),
            actor=actor,
        )


async def test_tip_does_not_change_commission(tip_session: AsyncSession) -> None:
    appointment_id, _staff_id = await _book(tip_session)
    actor = _admin()
    bookings = _bookings(tip_session)
    for target in _WORKFLOW:
        await bookings.change_status(appointment_id, target, actor=actor)
    await get_billing_service(tip_session).create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("400.00"),
            payment_method=PaymentMethod.CASH,
        ),
        actor=actor,
    )
    await _tips(tip_session).create_tip(
        TipCreateRequest(appointment_id=appointment_id, amount=Decimal("100.00")),
        actor=actor,
    )
    commissions = await get_commission_service(tip_session).list_commissions(
        PaginationParams(page=1, limit=10),
        actor=actor,
        appointment_id=appointment_id,
    )
    assert commissions.total == 1
    assert commissions.items[0].commission_amount == Decimal("160.00")
    assert commissions.items[0].service_revenue == Decimal("400.00")


async def test_staff_can_list_own_tips_but_cannot_write(tip_session: AsyncSession) -> None:
    appointment_id, staff_id = await _book(tip_session)
    admin = _admin()
    created = await _tips(tip_session).create_tip(
        TipCreateRequest(appointment_id=appointment_id, amount=Decimal("80.00")),
        actor=admin,
    )
    profile = await StaffRepository(tip_session).get_by_id(staff_id)
    assert profile is not None
    owner = CurrentUser(id=profile.user_id, roles=[RoleName.STAFF], email="priya@example.com")
    other_staff = await StaffService(StaffRepository(tip_session)).create_staff(
        StaffCreateRequest(
            name="Rohan Mehta",
            email="rohan@example.com",
            password="StaffPass123!",
            phone="9876500002",
            designation="Stylist",
            commission_percentage=Decimal("30.00"),
            joining_date=date(2024, 2, 1),
            status=StaffStatus.ACTIVE,
        ),
        actor=admin,
    )
    other = CurrentUser(
        id=other_staff.user_id,
        roles=[RoleName.STAFF],
        email="rohan@example.com",
    )
    tips = _tips(tip_session)
    own = await tips.list_staff_tips(staff_id, PaginationParams(page=1, limit=10), actor=owner)
    assert own.total == 1
    assert own.items[0].id == created.id
    with pytest.raises(PermissionDeniedException, match="own tips"):
        await tips.list_staff_tips(staff_id, PaginationParams(page=1, limit=10), actor=other)
