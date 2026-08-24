from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.appointments.models import Appointment
from app.appointments.models import AppointmentService as AppointmentLine
from app.billing.models import Invoice, Payment
from app.common.enums import PaymentStatus
from app.common.repository import BaseRepository
from app.customers.models import Customer
from app.staff.models import Staff


class InvoiceRepository(BaseRepository[Invoice]):
    """Database access for invoices."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Invoice)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Invoice]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(noload(Invoice.appointment))
        )

    async def get_by_appointment_id(self, appointment_id: UUID) -> Invoice | None:
        result = await self.session.execute(
            self._detail_stmt().where(Invoice.appointment_id == appointment_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_detail(self, invoice_id: UUID) -> Invoice | None:
        result = await self.session.execute(self._detail_stmt().where(Invoice.id == invoice_id))
        return result.unique().scalar_one_or_none()

    def _detail_stmt(self) -> Select[tuple[Invoice]]:
        return (
            select(Invoice)
            .where(Invoice.is_deleted.is_(False))
            .options(
                selectinload(Invoice.appointment).options(
                    selectinload(Appointment.appointment_services).options(
                        noload(AppointmentLine.appointment),
                        noload(AppointmentLine.service),
                    ),
                    noload(Appointment.customer),
                    noload(Appointment.staff),
                    noload(Appointment.payments),
                    noload(Appointment.commission),
                    noload(Appointment.tips),
                    noload(Appointment.invoice),
                )
            )
            .execution_options(populate_existing=True)
        )


class PaymentRepository(BaseRepository[Payment]):
    """Database access for payment history."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Payment)

    def _base_stmt(self, *, include_deleted: bool = False) -> Select[tuple[Payment]]:
        return (
            super()
            ._base_stmt(include_deleted=include_deleted)
            .options(noload(Payment.appointment))
        )

    async def sum_successful(self, appointment_id: UUID) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.appointment_id == appointment_id,
                Payment.payment_status == PaymentStatus.SUCCESS,
                Payment.is_deleted.is_(False),
            )
        )
        return Decimal(str(result.scalar_one())).quantize(Decimal("0.01"))


class BillingAppointmentRepository:
    """Appointment reads needed by billing without pulling the booking service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, appointment_id: UUID) -> Appointment | None:
        stmt = (
            select(Appointment)
            .where(Appointment.id == appointment_id, Appointment.is_deleted.is_(False))
            .options(
                selectinload(Appointment.appointment_services).options(
                    noload(AppointmentLine.appointment),
                    noload(AppointmentLine.service),
                ),
                selectinload(Appointment.customer).options(noload(Customer.appointments)),
                selectinload(Appointment.staff).options(
                    noload(Staff.user),
                    noload(Staff.schedules),
                    noload(Staff.appointments),
                    noload(Staff.commissions),
                    noload(Staff.tips),
                    noload(Staff.tasks),
                ),
                noload(Appointment.invoice),
                noload(Appointment.payments),
                noload(Appointment.commission),
                noload(Appointment.tips),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
