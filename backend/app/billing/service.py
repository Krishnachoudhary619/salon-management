from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.appointments.models import Appointment
from app.appointments.models import AppointmentService as AppointmentLine
from app.billing.models import Invoice, Payment
from app.billing.repository import (
    BillingAppointmentRepository,
    InvoiceRepository,
    PaymentRepository,
)
from app.billing.schemas import (
    InvoiceLineResponse,
    InvoiceResponse,
    PaymentCreateRequest,
    PaymentResponse,
)
from app.commissions.service import CommissionService
from app.common.enums import AppointmentStatus, PaymentMethod, PaymentStatus, SortOrder
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.customers.service import CustomerService

logger = get_logger(__name__)

_MONEY = Decimal("0.01")
_ALLOWED_PAYMENT_SORT = {"created_at", "paid_at", "amount", "payment_status", "payment_method"}
_ALLOWED_INVOICE_SORT = {"created_at", "invoice_number", "total", "updated_at"}
_CREATE_STATUSES = frozenset(
    {PaymentStatus.PENDING, PaymentStatus.SUCCESS, PaymentStatus.FAILED}
)
_BLOCKED_STATUSES = frozenset({AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW})


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_MONEY)


def _active_lines(appointment: Appointment) -> list[AppointmentLine]:
    return [line for line in appointment.appointment_services if not line.is_deleted]


def to_invoice_response(invoice: Invoice, *, paid_amount: Decimal) -> InvoiceResponse:
    appointment = invoice.appointment
    lines = _active_lines(appointment) if appointment is not None else []
    total = _money(invoice.total)
    paid = _money(paid_amount)
    return InvoiceResponse(
        id=invoice.id,
        appointment_id=invoice.appointment_id,
        invoice_number=invoice.invoice_number,
        subtotal=_money(invoice.subtotal),
        tax=_money(invoice.tax),
        total=total,
        paid_amount=paid,
        is_paid=paid >= total,
        line_items=[
            InvoiceLineResponse(
                service_id=line.service_id,
                service_name=line.service_name_snapshot,
                duration_minutes=line.duration_minutes_snapshot,
                price=_money(line.price_snapshot),
            )
            for line in sorted(lines, key=lambda item: item.created_at)
        ],
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


def to_payment_response(payment: Payment, *, invoice_id: UUID | None) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        appointment_id=payment.appointment_id,
        invoice_id=invoice_id,
        amount=_money(payment.amount),
        payment_method=payment.payment_method,
        payment_status=payment.payment_status,
        paid_at=payment.paid_at,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


class BillingService(BaseService[Payment]):
    """Invoice generation, payments, and payment history."""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        *,
        invoice_repository: InvoiceRepository,
        appointments: BillingAppointmentRepository,
        customer_service: CustomerService,
        commission_service: CommissionService,
    ) -> None:
        super().__init__(payment_repository, resource_name="Payment")
        self.payment_repository = payment_repository
        self.invoice_repository = invoice_repository
        self.appointments = appointments
        self.customer_service = customer_service
        self.commission_service = commission_service

    async def generate_invoice_for_appointment(
        self,
        appointment_id: UUID,
        *,
        actor: CurrentUser,
    ) -> InvoiceResponse:
        existing = await self.invoice_repository.get_by_appointment_id(appointment_id)
        if existing is not None:
            paid = await self.payment_repository.sum_successful(appointment_id)
            return to_invoice_response(existing, paid_amount=paid)

        appointment = await self._require_appointment(appointment_id)
        if appointment.status != AppointmentStatus.COMPLETED:
            raise ConflictException("Invoices are generated only for completed appointments")
        lines = _active_lines(appointment)
        if not lines:
            raise ValidationException("Cannot generate an invoice without services")
        subtotal = _money(sum((line.price_snapshot for line in lines), Decimal("0.00")))
        tax = _money(Decimal("0.00"))
        total = _money(subtotal + tax)
        if total <= 0:
            raise ValidationException("Invoice total must be greater than zero")
        created = await self.invoice_repository.create(
            Invoice(
                appointment_id=appointment.id,
                invoice_number=_next_invoice_number(),
                subtotal=subtotal,
                tax=tax,
                total=total,
            ),
            created_by=actor.id,
        )
        logger.info(
            "invoice_generated",
            invoice_id=str(created.id),
            appointment_id=str(appointment.id),
        )
        loaded = await self.invoice_repository.get_detail(created.id)
        assert loaded is not None
        return to_invoice_response(loaded, paid_amount=Decimal("0.00"))

    async def get_invoice(self, invoice_id: UUID) -> InvoiceResponse:
        invoice = await self.invoice_repository.get_detail(invoice_id)
        if invoice is None:
            raise NotFoundException("Invoice not found")
        paid = await self.payment_repository.sum_successful(invoice.appointment_id)
        return to_invoice_response(invoice, paid_amount=paid)

    async def list_invoices(
        self,
        params: PaginationParams,
        *,
        appointment_id: UUID | None = None,
    ) -> PaginatedData[InvoiceResponse]:
        if params.sort_by is None:
            params.sort_by = "created_at"
            params.sort_order = SortOrder.DESC
        filters = []
        if appointment_id is not None:
            filters.append(Invoice.appointment_id == appointment_id)
        page = await self.invoice_repository.list(
            params,
            filters=filters or None,
            search_fields=["invoice_number"],
            allowed_sort_fields=_ALLOWED_INVOICE_SORT,
        )
        items: list[InvoiceResponse] = []
        for invoice in page.items:
            paid = await self.payment_repository.sum_successful(invoice.appointment_id)
            detail = await self.invoice_repository.get_detail(invoice.id)
            assert detail is not None
            items.append(to_invoice_response(detail, paid_amount=paid))
        return PaginatedData(
            items=items,
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def list_payments(
        self,
        params: PaginationParams,
        *,
        appointment_id: UUID | None = None,
        payment_method: PaymentMethod | None = None,
        payment_status: PaymentStatus | None = None,
    ) -> PaginatedData[PaymentResponse]:
        if params.sort_by is None:
            params.sort_by = "created_at"
            params.sort_order = SortOrder.DESC
        filters = []
        if appointment_id is not None:
            filters.append(Payment.appointment_id == appointment_id)
        if payment_method is not None:
            filters.append(Payment.payment_method == payment_method)
        if payment_status is not None:
            filters.append(Payment.payment_status == payment_status)
        page = await self.payment_repository.list(
            params,
            filters=filters or None,
            allowed_sort_fields=_ALLOWED_PAYMENT_SORT,
        )
        items: list[PaymentResponse] = []
        for payment in page.items:
            invoice = await self.invoice_repository.get_by_appointment_id(payment.appointment_id)
            items.append(
                to_payment_response(payment, invoice_id=invoice.id if invoice else None)
            )
        return PaginatedData(
            items=items,
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def create_payment(
        self,
        payload: PaymentCreateRequest,
        *,
        actor: CurrentUser,
    ) -> PaymentResponse:
        if payload.payment_status not in _CREATE_STATUSES:
            raise ValidationException("Refunds cannot be created through this endpoint")
        appointment = await self._require_appointment(payload.appointment_id)
        if appointment.status in _BLOCKED_STATUSES:
            raise ConflictException("Cannot record a payment on a cancelled or no-show appointment")
        invoice = await self.invoice_repository.get_by_appointment_id(appointment.id)
        if invoice is None:
            raise ConflictException("Invoice has not been generated for this appointment")

        amount = _money(payload.amount)
        paid_at = datetime.now(UTC) if payload.payment_status == PaymentStatus.SUCCESS else None
        previous_paid = await self.payment_repository.sum_successful(appointment.id)
        created = await self.payment_repository.create(
            Payment(
                appointment_id=appointment.id,
                amount=amount,
                payment_method=payload.payment_method,
                payment_status=payload.payment_status,
                paid_at=paid_at,
            ),
            created_by=actor.id,
        )
        if payload.payment_status == PaymentStatus.SUCCESS:
            new_paid = previous_paid + amount
            invoice_total = _money(invoice.total)
            if previous_paid < invoice_total <= new_paid:
                visited_at = appointment.completed_at or datetime.now(UTC)
                await self.customer_service.record_visit(
                    appointment.customer_id,
                    amount=invoice_total,
                    visited_at=visited_at,
                    actor=actor,
                )
            if new_paid >= invoice_total:
                await self.commission_service.generate_for_appointment(
                    appointment.id,
                    actor=actor,
                )
        logger.info(
            "payment_created",
            payment_id=str(created.id),
            appointment_id=str(appointment.id),
            status=str(payload.payment_status),
        )
        return to_payment_response(created, invoice_id=invoice.id)

    async def _require_appointment(self, appointment_id: UUID) -> Appointment:
        appointment = await self.appointments.get(appointment_id)
        if appointment is None:
            raise NotFoundException("Appointment not found")
        return appointment


def _next_invoice_number() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"INV-{stamp}-{uuid4().hex[:8].upper()}"
