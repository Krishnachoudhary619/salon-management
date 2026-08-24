from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.appointments.models import Appointment
from app.appointments.models import AppointmentService as AppointmentLine
from app.billing.repository import (
    BillingAppointmentRepository,
    InvoiceRepository,
    PaymentRepository,
)
from app.commissions.models import Commission
from app.commissions.repository import CommissionRepository
from app.commissions.schemas import CommissionResponse
from app.common.enums import AppointmentStatus, Permission, SortOrder
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException, NotFoundException, PermissionDeniedException
from app.core.logging import get_logger
from app.core.permissions import has_permission
from app.core.security import CurrentUser
from app.staff.repository import StaffRepository

logger = get_logger(__name__)

_MONEY = Decimal("0.01")
_ALLOWED_SORT = {
    "created_at",
    "commission_amount",
    "commission_percentage",
    "service_revenue",
    "staff_id",
}


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_MONEY, rounding=ROUND_HALF_UP)


def _commission_amount(revenue: Decimal, percentage: Decimal) -> Decimal:
    return _money(revenue * percentage / Decimal("100"))


def _active_lines(appointment: Appointment) -> list[AppointmentLine]:
    return [line for line in appointment.appointment_services if not line.is_deleted]


def to_commission_response(commission: Commission) -> CommissionResponse:
    staff_name = commission.staff.name if commission.staff is not None else ""
    return CommissionResponse(
        id=commission.id,
        appointment_id=commission.appointment_id,
        staff_id=commission.staff_id,
        staff_name=staff_name,
        service_revenue=_money(commission.service_revenue),
        commission_percentage=_money(commission.commission_percentage),
        commission_amount=_money(commission.commission_amount),
        created_at=commission.created_at,
        updated_at=commission.updated_at,
    )


class CommissionService(BaseService[Commission]):
    """Permanent commission snapshots generated after a completed, paid appointment."""

    def __init__(
        self,
        repository: CommissionRepository,
        *,
        appointments: BillingAppointmentRepository,
        invoice_repository: InvoiceRepository,
        payment_repository: PaymentRepository,
        staff_repository: StaffRepository,
    ) -> None:
        super().__init__(repository, resource_name="Commission")
        self.commission_repository = repository
        self.appointments = appointments
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository
        self.staff_repository = staff_repository

    async def generate_for_appointment(
        self,
        appointment_id: UUID,
        *,
        actor: CurrentUser,
    ) -> CommissionResponse:
        existing = await self.commission_repository.get_by_appointment_id(appointment_id)
        if existing is not None:
            return to_commission_response(existing)

        appointment = await self.appointments.get(appointment_id)
        if appointment is None:
            raise NotFoundException("Appointment not found")
        if appointment.status != AppointmentStatus.COMPLETED:
            raise ConflictException("Commissions are generated only for completed appointments")
        invoice = await self.invoice_repository.get_by_appointment_id(appointment.id)
        if invoice is None:
            raise ConflictException("Invoice has not been generated for this appointment")
        paid = await self.payment_repository.sum_successful(appointment.id)
        if paid < _money(invoice.total):
            raise ConflictException(
                "Commission is generated only after successful payment covers the invoice"
            )

        staff = appointment.staff
        if staff is None:
            staff = await self.staff_repository.get_by_id(appointment.staff_id)
        if staff is None:
            raise NotFoundException("Staff not found")

        lines = _active_lines(appointment)
        revenue = _money(sum((line.price_snapshot for line in lines), Decimal("0")))
        if revenue <= 0:
            raise ConflictException("Cannot generate commission without service revenue")
        percentage = _money(staff.commission_percentage)
        created = await self.commission_repository.create(
            Commission(
                appointment_id=appointment.id,
                staff_id=staff.id,
                service_revenue=revenue,
                commission_percentage=percentage,
                commission_amount=_commission_amount(revenue, percentage),
            ),
            created_by=actor.id,
        )
        logger.info(
            "commission_generated",
            commission_id=str(created.id),
            appointment_id=str(appointment.id),
            staff_id=str(staff.id),
        )
        loaded = await self.commission_repository.get_by_id(created.id)
        assert loaded is not None
        return to_commission_response(loaded)

    async def get_commission(
        self,
        commission_id: UUID,
        *,
        actor: CurrentUser,
    ) -> CommissionResponse:
        commission = await self.get(commission_id)
        await self._ensure_can_access(commission, actor)
        return to_commission_response(commission)

    async def list_commissions(
        self,
        params: PaginationParams,
        *,
        actor: CurrentUser,
        staff_id: UUID | None = None,
        appointment_id: UUID | None = None,
    ) -> PaginatedData[CommissionResponse]:
        scoped_staff_id = await self._scoped_staff_id(actor, staff_id)
        if params.sort_by is None:
            params.sort_by = "created_at"
            params.sort_order = SortOrder.DESC
        filters = []
        if scoped_staff_id is not None:
            filters.append(Commission.staff_id == scoped_staff_id)
        if appointment_id is not None:
            filters.append(Commission.appointment_id == appointment_id)
        page = await self.commission_repository.list(
            params,
            filters=filters or None,
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_commission_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def list_staff_commissions(
        self,
        staff_id: UUID,
        params: PaginationParams,
        *,
        actor: CurrentUser,
    ) -> PaginatedData[CommissionResponse]:
        staff = await self.staff_repository.get_by_id(staff_id)
        if staff is None:
            raise NotFoundException("Staff not found")
        return await self.list_commissions(params, actor=actor, staff_id=staff_id)

    async def _scoped_staff_id(
        self,
        actor: CurrentUser,
        requested_staff_id: UUID | None,
    ) -> UUID | None:
        if has_permission(actor, Permission.COMMISSION_READ):
            return requested_staff_id
        profile = await self.staff_repository.get_by_user_id(actor.id)
        if profile is None:
            raise PermissionDeniedException("No staff profile is linked to this account")
        if requested_staff_id is not None and requested_staff_id != profile.id:
            raise PermissionDeniedException("You can only access your own commissions")
        return profile.id

    async def _ensure_can_access(self, commission: Commission, actor: CurrentUser) -> None:
        scoped = await self._scoped_staff_id(actor, None)
        if scoped is not None and commission.staff_id != scoped:
            raise PermissionDeniedException("You can only access your own commissions")
