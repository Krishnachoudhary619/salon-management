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
from app.billing.service import BillingService
from app.common.enums import AppointmentStatus, PaymentMethod, PaymentStatus, StaffStatus
from app.common.enums import Role as RoleName
from app.common.pagination import PaginationParams
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
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

_WORKFLOW = (
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.ARRIVED,
    AppointmentStatus.IN_PROGRESS,
    AppointmentStatus.COMPLETED,
)


@pytest.fixture
async def billing_session() -> AsyncGenerator[AsyncSession, None]:
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


def _billing(session: AsyncSession) -> BillingService:
    return get_billing_service(session)


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


async def _book(
    session: AsyncSession,
    *,
    start: str = "10:00:00",
) -> tuple[UUID, UUID]:
    staff_id, customer_id, hair_id = await _seed(session)
    created = await _bookings(session).create_appointment(
        AppointmentCreateRequest(
            customer_id=customer_id,
            staff_id=staff_id,
            appointment_date=date(2026, 8, 24),
            start_time=time.fromisoformat(start),
            service_ids=[hair_id],
        ),
        actor=_admin(),
    )
    return created.id, customer_id


async def _complete(session: AsyncSession, appointment_id: UUID) -> None:
    bookings = _bookings(session)
    actor = _admin()
    for target in _WORKFLOW:
        await bookings.change_status(appointment_id, target, actor=actor)


async def test_completion_generates_invoice_once(billing_session: AsyncSession) -> None:
    appointment_id, _customer_id = await _book(billing_session)
    billing = _billing(billing_session)
    actor = _admin()

    with pytest.raises(ConflictException, match="completed"):
        await billing.generate_invoice_for_appointment(appointment_id, actor=actor)

    await _complete(billing_session, appointment_id)
    first = await billing.generate_invoice_for_appointment(appointment_id, actor=actor)
    second = await billing.generate_invoice_for_appointment(appointment_id, actor=actor)
    assert first.id == second.id
    assert first.total == Decimal("400.00")
    assert first.tax == Decimal("0.00")
    assert first.paid_amount == Decimal("0.00")
    assert first.is_paid is False
    assert first.invoice_number.startswith("INV-")
    assert len(first.line_items) == 1
    assert first.line_items[0].service_name == "Hair Cut"
    assert first.line_items[0].price == Decimal("400.00")

    listed = await billing.list_invoices(
        PaginationParams(page=1, limit=10),
        appointment_id=appointment_id,
    )
    assert listed.total == 1
    loaded = await billing.get_invoice(first.id)
    assert loaded.invoice_number == first.invoice_number


async def test_cash_card_and_upi_success_payments(billing_session: AsyncSession) -> None:
    appointment_id, _customer_id = await _book(billing_session)
    await _complete(billing_session, appointment_id)
    billing = _billing(billing_session)
    actor = _admin()
    invoice = await billing.generate_invoice_for_appointment(appointment_id, actor=actor)

    cash = await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("150.00"),
            payment_method=PaymentMethod.CASH,
        ),
        actor=actor,
    )
    card = await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("150.00"),
            payment_method=PaymentMethod.CARD,
        ),
        actor=actor,
    )
    upi = await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.UPI,
        ),
        actor=actor,
    )
    assert cash.payment_status == PaymentStatus.SUCCESS
    assert cash.paid_at is not None
    assert cash.invoice_id == invoice.id
    assert card.payment_method == PaymentMethod.CARD
    assert upi.payment_method == PaymentMethod.UPI

    paid = await billing.get_invoice(invoice.id)
    assert paid.paid_amount == Decimal("400.00")
    assert paid.is_paid is True

    history = await billing.list_payments(
        PaginationParams(page=1, limit=10),
        appointment_id=appointment_id,
        payment_method=PaymentMethod.UPI,
    )
    assert history.total == 1
    assert history.items[0].id == upi.id


async def test_visit_is_recorded_once_when_invoice_is_covered(
    billing_session: AsyncSession,
) -> None:
    appointment_id, customer_id = await _book(billing_session)
    await _complete(billing_session, appointment_id)
    billing = _billing(billing_session)
    crm = CustomerService(CustomerRepository(billing_session))
    actor = _admin()

    await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("150.00"),
            payment_method=PaymentMethod.CASH,
        ),
        actor=actor,
    )
    after_partial = await crm.get_customer(customer_id)
    assert after_partial.visit_count == 0
    assert after_partial.total_spent == Decimal("0.00")

    await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("250.00"),
            payment_method=PaymentMethod.UPI,
        ),
        actor=actor,
    )
    after_paid = await crm.get_customer(customer_id)
    assert after_paid.visit_count == 1
    assert after_paid.total_spent == Decimal("400.00")
    assert after_paid.last_visit is not None

    await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("50.00"),
            payment_method=PaymentMethod.CARD,
        ),
        actor=actor,
    )
    after_overpay = await crm.get_customer(customer_id)
    assert after_overpay.visit_count == 1
    assert after_overpay.total_spent == Decimal("400.00")


async def test_payment_requires_invoice_and_rejects_refunds(
    billing_session: AsyncSession,
) -> None:
    appointment_id, _customer_id = await _book(billing_session)
    billing = _billing(billing_session)
    actor = _admin()
    payload = PaymentCreateRequest(
        appointment_id=appointment_id,
        amount=Decimal("400.00"),
        payment_method=PaymentMethod.CASH,
    )
    with pytest.raises(ConflictException, match="Invoice has not been generated"):
        await billing.create_payment(payload, actor=actor)

    cancelled = await _bookings(billing_session).cancel_appointment(appointment_id, actor=actor)
    assert cancelled.status == AppointmentStatus.CANCELLED
    with pytest.raises(ConflictException, match="cancelled or no-show"):
        await billing.create_payment(payload, actor=actor)

    with pytest.raises(ValidationException, match="Refunds"):
        await billing.create_payment(
            PaymentCreateRequest(
                appointment_id=appointment_id,
                amount=Decimal("400.00"),
                payment_method=PaymentMethod.CASH,
                payment_status=PaymentStatus.REFUNDED,
            ),
            actor=actor,
        )


async def test_failed_payment_does_not_cover_invoice(billing_session: AsyncSession) -> None:
    appointment_id, _customer_id = await _book(billing_session)
    await _complete(billing_session, appointment_id)
    billing = _billing(billing_session)
    actor = _admin()
    invoice = await billing.generate_invoice_for_appointment(appointment_id, actor=actor)
    failed = await billing.create_payment(
        PaymentCreateRequest(
            appointment_id=appointment_id,
            amount=Decimal("400.00"),
            payment_method=PaymentMethod.CARD,
            payment_status=PaymentStatus.FAILED,
        ),
        actor=actor,
    )
    assert failed.paid_at is None
    unpaid = await billing.get_invoice(invoice.id)
    assert unpaid.is_paid is False
    assert unpaid.paid_amount == Decimal("0.00")


async def test_unknown_invoice_is_not_found(billing_session: AsyncSession) -> None:
    with pytest.raises(NotFoundException, match="Invoice not found"):
        await _billing(billing_session).get_invoice(uuid4())
