from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.appointments.dependencies import get_appointment_service
from app.appointments.schemas import AppointmentCreateRequest
from app.billing.dependencies import get_billing_service
from app.billing.schemas import PaymentCreateRequest
from app.common.enums import AppointmentStatus, PaymentMethod, PaymentStatus, StaffStatus
from app.common.enums import Role as RoleName
from app.core.exceptions import ValidationException
from app.core.security import CurrentUser
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreateRequest
from app.customers.service import CustomerService
from app.dashboard.dependencies import get_dashboard_service
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

_WORKFLOW = (
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.ARRIVED,
    AppointmentStatus.IN_PROGRESS,
    AppointmentStatus.COMPLETED,
)


@pytest.fixture
async def dashboard_session() -> AsyncGenerator[AsyncSession, None]:
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


def _today() -> date:
    return datetime.now(UTC).date()


async def _seed(session: AsyncSession) -> tuple[UUID, UUID, UUID]:
    actor = _admin()
    today = _today()
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
            day_of_week=today.weekday(),
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


async def _complete_and_pay(session: AsyncSession, appointment_id: UUID) -> None:
    actor = _admin()
    bookings = get_appointment_service(session)
    for target in _WORKFLOW:
        await bookings.change_status(appointment_id, target, actor=actor)
    await get_billing_service(session).create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("400.00"),
            payment_method=PaymentMethod.CASH,
        ),
        actor=actor,
    )


async def test_empty_overview_is_zero(dashboard_session: AsyncSession) -> None:
    overview = await get_dashboard_service(dashboard_session).get_overview()
    assert overview.revenue_today == Decimal("0.00")
    assert overview.revenue_this_month == Decimal("0.00")
    assert overview.appointments_today == 0
    assert overview.customers_served == 0
    assert overview.average_ticket_size == Decimal("0.00")


async def test_overview_uses_sql_aggregates_after_paid_visit(
    dashboard_session: AsyncSession,
) -> None:
    staff_id, customer_id, hair_id = await _seed(dashboard_session)
    actor = _admin()
    today = _today()
    created = await get_appointment_service(dashboard_session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=today,
            start_time=time(10, 0),
            service_ids=[hair_id],
        ),
        actor=actor,
    )
    await _complete_and_pay(dashboard_session, created.id)

    dashboard = get_dashboard_service(dashboard_session)
    overview = await dashboard.get_overview()
    assert overview.revenue_today == Decimal("400.00")
    assert overview.revenue_this_month == Decimal("400.00")
    assert overview.appointments_today == 1
    assert overview.customers_served == 1
    assert overview.average_ticket_size == Decimal("400.00")

    revenue = await dashboard.get_revenue_series(group_by="day")
    assert any(
        item.period == today.isoformat() and item.revenue == Decimal("400.00")
        for item in revenue.items
    )
    monthly = await dashboard.get_revenue_series(group_by="month")
    assert monthly.items[0].period == today.strftime("%Y-%m")
    assert monthly.items[0].revenue == Decimal("400.00")

    volume = await dashboard.get_appointment_series()
    assert volume.items[0].appointment_date == today
    assert volume.items[0].completed == 1

    top = await dashboard.get_top_performers()
    assert len(top.items) == 1
    assert top.items[0].staff_id == staff_id
    assert top.items[0].staff_name == "Priya Sharma"
    assert top.items[0].revenue == Decimal("400.00")
    assert top.items[0].appointments_completed == 1


async def test_failed_payment_is_excluded_from_revenue(
    dashboard_session: AsyncSession,
) -> None:
    staff_id, customer_id, hair_id = await _seed(dashboard_session)
    actor = _admin()
    created = await get_appointment_service(dashboard_session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=_today(),
            start_time=time(10, 0),
            service_ids=[hair_id],
        ),
        actor=actor,
    )
    bookings = get_appointment_service(dashboard_session)
    for target in _WORKFLOW:
        await bookings.change_status(created.id, target, actor=actor)
    await get_billing_service(dashboard_session).create_payment(
        PaymentCreateRequest(
            appointment_id=created.id,
            amount=Decimal("400.00"),
            payment_method=PaymentMethod.CARD,
            payment_status=PaymentStatus.FAILED,
        ),
        actor=actor,
    )
    overview = await get_dashboard_service(dashboard_session).get_overview()
    assert overview.revenue_today == Decimal("0.00")
    assert overview.appointments_today == 1
    assert overview.customers_served == 1
    assert overview.average_ticket_size == Decimal("400.00")


async def test_invalid_range_is_rejected(dashboard_session: AsyncSession) -> None:
    dashboard = get_dashboard_service(dashboard_session)
    with pytest.raises(ValidationException, match="on or before"):
        await dashboard.get_revenue_series(
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 1),
        )
