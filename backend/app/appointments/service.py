from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from app.appointments.duration import add_minutes
from app.appointments.engine import AvailabilityEngine
from app.appointments.models import Appointment
from app.appointments.models import AppointmentService as AppointmentLine
from app.appointments.repository import AppointmentRepository
from app.appointments.schemas import (
    AppointmentCreateRequest,
    AppointmentLineResponse,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    AppointmentUpdateRequest,
    CalendarDayResponse,
    CalendarResponse,
)
from app.appointments.workflow import (
    RESCHEDULABLE_STATUSES,
    TERMINAL_STATUSES,
    as_status,
    can_transition,
)
from app.billing.service import BillingService
from app.common.enums import AppointmentStatus, Permission, SortOrder
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.logging import get_logger
from app.core.permissions import has_permission
from app.core.security import CurrentUser
from app.customers.service import CustomerService
from app.services.models import Service
from app.staff.repository import StaffRepository

logger = get_logger(__name__)

_ALLOWED_SORT = {
    "appointment_date",
    "start_time",
    "end_time",
    "status",
    "created_at",
    "updated_at",
}
_MAX_CALENDAR_DAYS = 42


def _active_lines(appointment: Appointment) -> list[AppointmentLine]:
    return [line for line in appointment.appointment_services if not line.is_deleted]


def to_appointment_response(appointment: Appointment) -> AppointmentResponse:
    lines = sorted(_active_lines(appointment), key=lambda item: item.created_at)
    duration = sum(line.duration_minutes_snapshot for line in lines)
    customer_name = appointment.customer.name if appointment.customer is not None else ""
    customer_phone = appointment.customer.phone if appointment.customer is not None else ""
    staff_name = appointment.staff.name if appointment.staff is not None else ""
    return AppointmentResponse(
        id=appointment.id,
        customer_id=appointment.customer_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        staff_id=appointment.staff_id,
        staff_name=staff_name,
        appointment_date=appointment.appointment_date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=as_status(appointment.status),
        notes=appointment.notes,
        duration_minutes=duration,
        services=[
            AppointmentLineResponse(
                id=line.id,
                service_id=line.service_id,
                service_name=line.service_name_snapshot,
                duration_minutes=line.duration_minutes_snapshot,
                price=line.price_snapshot,
            )
            for line in lines
        ],
        cancelled_at=appointment.cancelled_at,
        completed_at=appointment.completed_at,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


class AppointmentService(BaseService[Appointment]):
    """Booking rules: availability, duration snapshots, and status workflow."""

    def __init__(
        self,
        repository: AppointmentRepository,
        *,
        availability_engine: AvailabilityEngine,
        customer_service: CustomerService,
        staff_repository: StaffRepository,
        billing_service: BillingService,
    ) -> None:
        super().__init__(repository, resource_name="Appointment")
        self.appointment_repository = repository
        self.availability_engine = availability_engine
        self.customer_service = customer_service
        self.staff_repository = staff_repository
        self.billing_service = billing_service

    async def get_appointment(
        self,
        appointment_id: UUID,
        *,
        actor: CurrentUser,
    ) -> AppointmentResponse:
        appointment = await self.get(appointment_id)
        await self._ensure_can_access(appointment, actor, write=False)
        return to_appointment_response(appointment)

    async def list_appointments(
        self,
        params: PaginationParams,
        *,
        actor: CurrentUser,
        staff_id: UUID | None = None,
        customer_id: UUID | None = None,
        status: AppointmentStatus | None = None,
        appointment_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> PaginatedData[AppointmentResponse]:
        scoped_staff_id = await self._scoped_staff_id(actor, staff_id, write=False)
        if params.sort_by is None:
            params.sort_by = "appointment_date"
            params.sort_order = SortOrder.DESC
        filters = []
        if scoped_staff_id is not None:
            filters.append(Appointment.staff_id == scoped_staff_id)
        if customer_id is not None:
            filters.append(Appointment.customer_id == customer_id)
        if status is not None:
            filters.append(Appointment.status == status)
        if appointment_date is not None:
            filters.append(Appointment.appointment_date == appointment_date)
        if date_from is not None:
            filters.append(Appointment.appointment_date >= date_from)
        if date_to is not None:
            filters.append(Appointment.appointment_date <= date_to)
        page = await self.appointment_repository.list(
            params,
            filters=filters or None,
            search_fields=["customer_name", "customer_phone"],
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_appointment_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def get_calendar(
        self,
        *,
        actor: CurrentUser,
        start_date: date,
        end_date: date,
        staff_id: UUID | None = None,
    ) -> CalendarResponse:
        if end_date < start_date:
            raise ValidationException("end_date must be on or after start_date")
        if (end_date - start_date).days + 1 > _MAX_CALENDAR_DAYS:
            raise ValidationException(f"Calendar range cannot exceed {_MAX_CALENDAR_DAYS} days")
        scoped_staff_id = await self._scoped_staff_id(actor, staff_id, write=False)
        rows = await self.appointment_repository.list_in_range(
            start_date,
            end_date,
            staff_id=scoped_staff_id,
        )
        grouped: dict[date, list[AppointmentResponse]] = {}
        current = start_date
        while current <= end_date:
            grouped[current] = []
            current += timedelta(days=1)
        for row in rows:
            grouped[row.appointment_date].append(to_appointment_response(row))
        return CalendarResponse(
            start_date=start_date,
            end_date=end_date,
            days=[
                CalendarDayResponse(date=day, appointments=items)
                for day, items in grouped.items()
            ],
        )

    async def create_appointment(
        self,
        payload: AppointmentCreateRequest,
        *,
        actor: CurrentUser,
    ) -> AppointmentResponse:
        staff_id = await self._staff_id_for_write(actor, payload.staff_id)
        customer_id = await self._resolve_customer_id(payload, actor)
        catalog = await self._load_catalog_services(payload.service_ids)
        duration = sum(item.duration_minutes for item in catalog)
        end_time = self._end_time(payload.start_time, duration)
        await self.availability_engine.validate_slot(
            staff_id=staff_id,
            on_date=payload.appointment_date,
            start_time=payload.start_time,
            end_time=end_time,
            duration_minutes=duration,
        )
        created = await self.appointment_repository.create(
            Appointment(
                customer_id=customer_id,
                staff_id=staff_id,
                appointment_date=payload.appointment_date,
                start_time=payload.start_time,
                end_time=end_time,
                status=AppointmentStatus.PENDING,
                notes=payload.notes,
            ),
            created_by=actor.id,
        )
        await self._write_lines(created.id, catalog, actor_id=actor.id)
        self.appointment_repository.session.expire(
            created,
            ["appointment_services", "customer", "staff"],
        )
        loaded = await self.appointment_repository.get_by_id(created.id)
        assert loaded is not None
        logger.info("appointment_created", appointment_id=str(created.id))
        return to_appointment_response(loaded)

    async def update_appointment(
        self,
        appointment_id: UUID,
        payload: AppointmentUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> AppointmentResponse:
        appointment = await self.get(appointment_id)
        await self._ensure_can_access(appointment, actor, write=True)
        if appointment.status in TERMINAL_STATUSES:
            raise ConflictException(
                "A completed, cancelled, or no-show appointment cannot be edited"
            )
        changes = payload.model_dump(exclude_unset=True)
        staff_id = appointment.staff_id
        if "staff_id" in changes and changes["staff_id"] is not None:
            staff_id = await self._staff_id_for_write(actor, changes["staff_id"])
            appointment.staff_id = staff_id
        if "customer_id" in changes and changes["customer_id"] is not None:
            await self.customer_service.get_customer(changes["customer_id"])
            appointment.customer_id = changes["customer_id"]
        if "notes" in changes:
            appointment.notes = changes["notes"]
        catalog: list[Service] | None = None
        if "service_ids" in changes:
            if appointment.status not in RESCHEDULABLE_STATUSES:
                raise ConflictException("Services cannot be changed for this appointment")
            catalog = await self._load_catalog_services(changes["service_ids"])
            duration = sum(item.duration_minutes for item in catalog)
            appointment.end_time = self._end_time(appointment.start_time, duration)
        needs_slot = "staff_id" in changes or "service_ids" in changes
        if needs_slot:
            await self.availability_engine.validate_slot(
                staff_id=staff_id,
                on_date=appointment.appointment_date,
                start_time=appointment.start_time,
                end_time=appointment.end_time,
                exclude_appointment_id=appointment.id,
            )
        if catalog is not None:
            await self._replace_lines(appointment.id, catalog, actor_id=actor.id)
        await self.appointment_repository.update(appointment, updated_by=actor.id)
        self.appointment_repository.session.expire(
            appointment,
            ["appointment_services", "customer", "staff"],
        )
        loaded = await self.appointment_repository.get_by_id(appointment.id)
        assert loaded is not None
        logger.info("appointment_updated", appointment_id=str(appointment.id))
        return to_appointment_response(loaded)

    async def change_status(
        self,
        appointment_id: UUID,
        target: AppointmentStatus,
        *,
        actor: CurrentUser,
        staff_id: UUID | None = None,
    ) -> AppointmentResponse:
        appointment = await self.get(appointment_id)
        await self._ensure_can_access(appointment, actor, write=True)
        current = as_status(appointment.status)
        if not can_transition(current, target):
            raise ValidationException(
                f"Cannot change status from {current.value} to {target.value}"
            )
        if staff_id is not None:
            if target != AppointmentStatus.CONFIRMED:
                raise ValidationException("Staff can only be assigned when confirming")
            assigned = await self._staff_id_for_write(actor, staff_id)
            if assigned != appointment.staff_id:
                appointment.staff_id = assigned
                await self.availability_engine.validate_slot(
                    staff_id=assigned,
                    on_date=appointment.appointment_date,
                    start_time=appointment.start_time,
                    end_time=appointment.end_time,
                    exclude_appointment_id=appointment.id,
                )
        appointment.status = target
        if target == AppointmentStatus.CANCELLED:
            appointment.cancelled_at = datetime.now(UTC)
        if target == AppointmentStatus.COMPLETED:
            appointment.completed_at = datetime.now(UTC)
        await self.appointment_repository.update(appointment, updated_by=actor.id)
        if staff_id is not None:
            self.appointment_repository.session.expire(appointment, ["staff"])
        if target == AppointmentStatus.COMPLETED:
            await self.billing_service.generate_invoice_for_appointment(
                appointment.id,
                actor=actor,
            )
        loaded = await self.appointment_repository.get_by_id(appointment.id)
        assert loaded is not None
        logger.info(
            "appointment_status_changed",
            appointment_id=str(appointment.id),
            status=target.value,
        )
        return to_appointment_response(loaded)

    async def cancel_appointment(
        self,
        appointment_id: UUID,
        *,
        actor: CurrentUser,
    ) -> AppointmentResponse:
        return await self.change_status(
            appointment_id,
            AppointmentStatus.CANCELLED,
            actor=actor,
        )

    async def reschedule_appointment(
        self,
        appointment_id: UUID,
        payload: AppointmentRescheduleRequest,
        *,
        actor: CurrentUser,
    ) -> AppointmentResponse:
        appointment = await self.get(appointment_id)
        await self._ensure_can_access(appointment, actor, write=True)
        if appointment.status not in RESCHEDULABLE_STATUSES:
            raise ConflictException("This appointment cannot be rescheduled")
        staff_id = appointment.staff_id
        if payload.staff_id is not None:
            staff_id = await self._staff_id_for_write(actor, payload.staff_id)
        duration = sum(line.duration_minutes_snapshot for line in _active_lines(appointment))
        end_time = self._end_time(payload.start_time, duration)
        await self.availability_engine.validate_slot(
            staff_id=staff_id,
            on_date=payload.appointment_date,
            start_time=payload.start_time,
            end_time=end_time,
            duration_minutes=duration,
            exclude_appointment_id=appointment.id,
        )
        appointment.staff_id = staff_id
        appointment.appointment_date = payload.appointment_date
        appointment.start_time = payload.start_time
        appointment.end_time = end_time
        await self.appointment_repository.update(appointment, updated_by=actor.id)
        self.appointment_repository.session.expire(
            appointment,
            ["appointment_services", "customer", "staff"],
        )
        loaded = await self.appointment_repository.get_by_id(appointment.id)
        assert loaded is not None
        logger.info("appointment_rescheduled", appointment_id=str(appointment.id))
        return to_appointment_response(loaded)

    def _end_time(self, start_time: time, duration_minutes: int) -> time:
        try:
            return add_minutes(start_time, duration_minutes)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc

    async def _resolve_customer_id(
        self,
        payload: AppointmentCreateRequest,
        actor: CurrentUser,
    ) -> UUID:
        if payload.customer_id is not None:
            existing = await self.customer_service.get_customer(payload.customer_id)
            return existing.id
        assert payload.customer is not None
        created = await self.customer_service.get_or_create_by_phone(payload.customer, actor=actor)
        return created.id

    async def _load_catalog_services(self, service_ids: list[UUID]) -> list[Service]:
        catalog = await self.appointment_repository.get_catalog_services(service_ids)
        found_ids = {item.id for item in catalog}
        missing = [str(service_id) for service_id in service_ids if service_id not in found_ids]
        if missing:
            raise NotFoundException("Service not found")
        inactive = [item.name for item in catalog if not item.is_active]
        if inactive:
            raise ConflictException("One or more services are not active")
        return catalog

    async def _write_lines(
        self,
        appointment_id: UUID,
        catalog: list[Service],
        *,
        actor_id: UUID,
    ) -> None:
        for item in catalog:
            await self.appointment_repository.add_line(
                AppointmentLine(
                    appointment_id=appointment_id,
                    service_id=item.id,
                    service_name_snapshot=item.name,
                    duration_minutes_snapshot=item.duration_minutes,
                    price_snapshot=item.price,
                ),
                created_by=actor_id,
            )

    async def _replace_lines(
        self,
        appointment_id: UUID,
        catalog: list[Service],
        *,
        actor_id: UUID,
    ) -> None:
        existing = await self.appointment_repository.list_lines(
            appointment_id,
            include_deleted=True,
        )
        by_service = {line.service_id: line for line in existing}
        keep_ids = {item.id for item in catalog}
        for item in catalog:
            line = by_service.get(item.id)
            if line is None:
                await self.appointment_repository.add_line(
                    AppointmentLine(
                        appointment_id=appointment_id,
                        service_id=item.id,
                        service_name_snapshot=item.name,
                        duration_minutes_snapshot=item.duration_minutes,
                        price_snapshot=item.price,
                    ),
                    created_by=actor_id,
                )
                continue
            line.is_deleted = False
            line.deleted_at = None
            line.service_name_snapshot = item.name
            line.duration_minutes_snapshot = item.duration_minutes
            line.price_snapshot = item.price
            line.updated_by = actor_id
            await self.appointment_repository.session.flush()
        for line in existing:
            if line.service_id not in keep_ids and not line.is_deleted:
                await self.appointment_repository.soft_delete_line(line, deleted_by=actor_id)

    async def _scoped_staff_id(
        self,
        actor: CurrentUser,
        requested_staff_id: UUID | None,
        *,
        write: bool,
    ) -> UUID | None:
        full = Permission.APPOINTMENT_WRITE if write else Permission.APPOINTMENT_READ
        if has_permission(actor, full):
            return requested_staff_id
        profile = await self.staff_repository.get_by_user_id(actor.id)
        if profile is None:
            raise PermissionDeniedException("No staff profile is linked to this account")
        if requested_staff_id is not None and requested_staff_id != profile.id:
            raise PermissionDeniedException("You can only access your own appointments")
        return profile.id

    async def _staff_id_for_write(self, actor: CurrentUser, staff_id: UUID) -> UUID:
        scoped = await self._scoped_staff_id(actor, staff_id, write=True)
        assert scoped is not None
        return scoped

    async def _ensure_can_access(
        self,
        appointment: Appointment,
        actor: CurrentUser,
        *,
        write: bool,
    ) -> None:
        scoped = await self._scoped_staff_id(actor, None, write=write)
        if scoped is not None and appointment.staff_id != scoped:
            raise PermissionDeniedException("You can only access your own appointments")
