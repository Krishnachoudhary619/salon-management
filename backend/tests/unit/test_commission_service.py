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
from app.commissions.service import CommissionService, _commission_amount
from app.common.enums import AppointmentStatus, PaymentMethod, PaymentStatus, StaffStatus
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
from app.staff.schemas import StaffCreateRequest, StaffUpdateRequest
from app.staff.service import StaffService
from app.users.models import Role

_WORKFLOW = (
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.ARRIVED,
    AppointmentStatus.IN_PROGRESS,
    AppointmentStatus.COMPLETED,
)


@pytest.fixture
async def commission_session() -> AsyncGenerator[AsyncSession, None]:
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


def _billing(session: AsyncSession):
    return get_billing_service(session)


def _commissions(session: AsyncSession) -> CommissionService:
    return get_commission_service(session)


async def _seed(
    session: AsyncSession,
    *,
    rate: Decimal = Decimal("40.00"),
) -> tuple[UUID, UUID, UUID]:
    actor = _admin()
    staff = await StaffService(StaffRepository(session)).create_staff(
        StaffCreateRequest(
            name="Priya Sharma",
            email="priya@example.com",
            password="StaffPass123!",
            phone="9876500001",
            designation="Senior Stylist",
            commission_percentage=rate,
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


async def _book(
    session: AsyncSession,
    staff_id: UUID,
    customer_id: UUID,
    service_id: UUID,
    *,
    start: str = "10:00:00",
) -> UUID:
    created = await _bookings(session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=date(2026, 8, 24),
            start_time=time.fromisoformat(start),
            service_ids=[service_id],
        ),
        actor=_admin(),
    )
    return created.id


async def _complete(session: AsyncSession, appointment_id: UUID) -> None:
    bookings = _bookings(session)
    actor = _admin()
    for target in _WORKFLOW:
        await bookings.change_status(appointment_id, target, actor=actor)


async def _pay(
    session: AsyncSession,
    appointment_id: UUID,
    *,
    amount: Decimal = Decimal("400.00"),
    status: PaymentStatus = PaymentStatus.SUCCESS,
) -> None:
    await _billing(session).create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=amount,
            payment_method=PaymentMethod.CASH,
            payment_status=status,
        ),
        actor=_admin(),
    )


def test_formula_rounds_half_up() -> None:
    assert _commission_amount(Decimal("400.00"), Decimal("40.00")) == Decimal("160.00")
    assert _commission_amount(Decimal("10.00"), Decimal("33.33")) == Decimal("3.33")
    assert _commission_amount(Decimal("10.00"), Decimal("33.35")) == Decimal("3.34")


async def test_commission_generated_once_when_completed_and_paid(
    commission_session: AsyncSession,
) -> None:
    staff_id, customer_id, hair_id = await _seed(commission_session)
    appointment_id = await _book(commission_session, staff_id, customer_id, hair_id)
    commissions = _commissions(commission_session)
    actor = _admin()

    with pytest.raises(ConflictException, match="completed"):
        await commissions.generate_for_appointment(appointment_id, actor=actor)

    await _complete(commission_session, appointment_id)
    with pytest.raises(ConflictException, match="successful payment"):
        await commissions.generate_for_appointment(appointment_id, actor=actor)

    await _pay(commission_session, appointment_id, amount=Decimal("150.00"))
    listed = await commissions.list_commissions(PaginationParams(page=1, limit=10), actor=actor)
    assert listed.total == 0

    await _pay(commission_session, appointment_id, amount=Decimal("250.00"))
    page = await commissions.list_commissions(
        PaginationParams(page=1, limit=10),
        actor=actor,
        appointment_id=appointment_id,
    )
    assert page.total == 1
    item = page.items[0]
    assert item.staff_id == staff_id
    assert item.staff_name == "Priya Sharma"
    assert item.service_revenue == Decimal("400.00")
    assert item.commission_percentage == Decimal("40.00")
    assert item.commission_amount == Decimal("160.00")

    again = await commissions.generate_for_appointment(appointment_id, actor=actor)
    assert again.id == item.id
    assert again.commission_amount == Decimal("160.00")


async def test_failed_payment_does_not_generate_commission(
    commission_session: AsyncSession,
) -> None:
    staff_id, customer_id, hair_id = await _seed(commission_session)
    appointment_id = await _book(commission_session, staff_id, customer_id, hair_id)
    await _complete(commission_session, appointment_id)
    await _pay(
        commission_session,
        appointment_id,
        amount=Decimal("400.00"),
        status=PaymentStatus.FAILED,
    )
    listed = await _commissions(commission_session).list_commissions(
        PaginationParams(page=1, limit=10),
        actor=_admin(),
    )
    assert listed.total == 0


async def test_historical_rate_is_not_recalculated(commission_session: AsyncSession) -> None:
    staff_id, customer_id, hair_id = await _seed(commission_session)
    first = await _book(commission_session, staff_id, customer_id, hair_id, start="10:00:00")
    await _complete(commission_session, first)
    await _pay(commission_session, first)

    await StaffService(StaffRepository(commission_session)).update_staff(
        staff_id,
        StaffUpdateRequest(commission_percentage=Decimal("50.00")),
        actor=_admin(),
    )
    second = await _book(commission_session, staff_id, customer_id, hair_id, start="11:00:00")
    await _complete(commission_session, second)
    await _pay(commission_session, second)

    commissions = _commissions(commission_session)
    actor = _admin()
    first_row = await commissions.list_commissions(
        PaginationParams(page=1, limit=10),
        actor=actor,
        appointment_id=first,
    )
    second_row = await commissions.list_commissions(
        PaginationParams(page=1, limit=10),
        actor=actor,
        appointment_id=second,
    )
    assert first_row.items[0].commission_percentage == Decimal("40.00")
    assert first_row.items[0].commission_amount == Decimal("160.00")
    assert second_row.items[0].commission_percentage == Decimal("50.00")
    assert second_row.items[0].commission_amount == Decimal("200.00")


async def test_staff_can_only_list_own_commissions(commission_session: AsyncSession) -> None:
    staff_id, customer_id, hair_id = await _seed(commission_session)
    appointment_id = await _book(commission_session, staff_id, customer_id, hair_id)
    await _complete(commission_session, appointment_id)
    await _pay(commission_session, appointment_id)

    profile = await StaffRepository(commission_session).get_by_id(staff_id)
    assert profile is not None
    owner = CurrentUser(id=profile.user_id, roles=[RoleName.STAFF], email="priya@example.com")
    other_staff = await StaffService(StaffRepository(commission_session)).create_staff(
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
        actor=_admin(),
    )
    other = CurrentUser(
        id=other_staff.user_id,
        roles=[RoleName.STAFF],
        email="rohan@example.com",
    )
    receptionist = CurrentUser(
        id=uuid4(),
        roles=[RoleName.RECEPTIONIST],
        email="desk@example.com",
    )
    commissions = _commissions(commission_session)

    own = await commissions.list_staff_commissions(
        staff_id,
        PaginationParams(page=1, limit=10),
        actor=owner,
    )
    assert own.total == 1

    with pytest.raises(PermissionDeniedException, match="own commissions"):
        await commissions.list_staff_commissions(
            staff_id,
            PaginationParams(page=1, limit=10),
            actor=other,
        )
    with pytest.raises(PermissionDeniedException):
        await commissions.list_commissions(PaginationParams(page=1, limit=10), actor=receptionist)
