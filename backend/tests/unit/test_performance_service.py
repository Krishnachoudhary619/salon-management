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
from app.common.enums import AppointmentStatus, PaymentMethod, StaffStatus
from app.common.enums import Role as RoleName
from app.core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from app.core.security import CurrentUser
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreateRequest
from app.customers.service import CustomerService
from app.database import models as _models  # noqa: F401
from app.database.base import Base
from app.performance.dependencies import get_performance_service
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
from app.tips.schemas import TipCreateRequest
from app.users.models import Role

_WORKFLOW = (
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.ARRIVED,
    AppointmentStatus.IN_PROGRESS,
    AppointmentStatus.COMPLETED,
)


@pytest.fixture
async def performance_session() -> AsyncGenerator[AsyncSession, None]:
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


async def _seed(session: AsyncSession) -> tuple[UUID, UUID, UUID, UUID]:
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
    return staff.id, staff.user_id, customer.id, hair.id


async def _complete_pay_and_tip(session: AsyncSession, appointment_id: UUID) -> None:
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
    await get_tip_service(session).create_tip(
        TipCreateRequest(appointment_id=appointment_id, amount=Decimal("100.00")),
        actor=actor,
    )


async def test_empty_team_has_no_staff(performance_session: AsyncSession) -> None:
    team = await get_performance_service(performance_session).get_team_performance()
    assert team.items == []


async def test_team_metrics_after_paid_visit_and_tip(
    performance_session: AsyncSession,
) -> None:
    staff_id, _user_id, customer_id, hair_id = await _seed(performance_session)
    actor = _admin()
    today = _today()
    created = await get_appointment_service(performance_session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=today,
            start_time=time(10, 0),
            service_ids=[hair_id],
        ),
        actor=actor,
    )
    await _complete_pay_and_tip(performance_session, created.id)
    await StaffService(StaffRepository(performance_session)).create_staff(
        StaffCreateRequest(
            name="Amit Kumar",
            email="amit@example.com",
            password="StaffPass123!",
            phone="9876500002",
            designation="Junior Stylist",
            commission_percentage=Decimal("20.00"),
            joining_date=date(2024, 6, 1),
            status=StaffStatus.ACTIVE,
        ),
        actor=actor,
    )

    team = await get_performance_service(performance_session).get_team_performance()
    assert team.start_date == date(today.year, today.month, 1)
    assert team.end_date == today
    assert [item.staff_name for item in team.items] == ["Priya Sharma", "Amit Kumar"]
    priya = team.items[0]
    assert priya.staff_id == staff_id
    assert priya.revenue_generated == Decimal("400.00")
    assert priya.customers_served == 1
    assert priya.appointments_completed == 1
    assert priya.tips_earned == Decimal("100.00")
    assert priya.commission_earned == Decimal("160.00")
    idle = team.items[1]
    assert idle.revenue_generated == Decimal("0.00")
    assert idle.customers_served == 0
    assert idle.appointments_completed == 0
    assert idle.tips_earned == Decimal("0.00")
    assert idle.commission_earned == Decimal("0.00")


async def test_staff_detail_and_own_access(performance_session: AsyncSession) -> None:
    staff_id, user_id, customer_id, hair_id = await _seed(performance_session)
    actor = _admin()
    created = await get_appointment_service(performance_session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=_today(),
            start_time=time(10, 0),
            service_ids=[hair_id],
        ),
        actor=actor,
    )
    await _complete_pay_and_tip(performance_session, created.id)
    other = await StaffService(StaffRepository(performance_session)).create_staff(
        StaffCreateRequest(
            name="Amit Kumar",
            email="amit@example.com",
            password="StaffPass123!",
            phone="9876500002",
            designation="Junior Stylist",
            commission_percentage=Decimal("20.00"),
            joining_date=date(2024, 6, 1),
            status=StaffStatus.ACTIVE,
        ),
        actor=actor,
    )

    performance = get_performance_service(performance_session)
    detail = await performance.get_staff_performance(staff_id, actor=actor)
    assert detail.staff_id == staff_id
    assert detail.revenue_generated == Decimal("400.00")
    assert detail.tips_earned == Decimal("100.00")
    assert detail.commission_earned == Decimal("160.00")

    owner = CurrentUser(id=user_id, roles=[RoleName.STAFF], email="priya@example.com")
    own = await performance.get_staff_performance(staff_id, actor=owner)
    assert own.appointments_completed == 1

    with pytest.raises(PermissionDeniedException, match="own performance"):
        await performance.get_staff_performance(other.id, actor=owner)
    with pytest.raises(NotFoundException, match="Staff not found"):
        await performance.get_staff_performance(uuid4(), actor=actor)


async def test_invalid_range_is_rejected(performance_session: AsyncSession) -> None:
    performance = get_performance_service(performance_session)
    with pytest.raises(ValidationException, match="on or before"):
        await performance.get_team_performance(
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 1),
        )
    with pytest.raises(ValidationException, match="366 days"):
        await performance.get_team_performance(
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 2),
        )
