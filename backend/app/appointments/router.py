from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.appointments.dependencies import AppointmentServiceDep
from app.appointments.schemas import (
    AppointmentCreateRequest,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    AppointmentStatusRequest,
    AppointmentUpdateRequest,
    CalendarResponse,
)
from app.common.dependencies import PaginationDep
from app.common.enums import AppointmentStatus, Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser

router = APIRouter(prefix="/appointments", tags=["Appointments"])

_READ = require_permissions(
    Permission.APPOINTMENT_READ,
    Permission.APPOINTMENT_READ_OWN,
    any_of=True,
)
_WRITE = require_permissions(
    Permission.APPOINTMENT_WRITE,
    Permission.APPOINTMENT_WRITE_OWN,
    any_of=True,
)


@router.get(
    "",
    summary="List appointments",
    description="Paginated bookings. Staff callers only see their own appointments.",
    response_model=APIResponse[PaginatedData[AppointmentResponse]],
)
async def list_appointments(
    pagination: PaginationDep,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_READ),
    staff_id: UUID | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    appointment_status: AppointmentStatus | None = Query(default=None, alias="status"),
    appointment_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> APIResponse[PaginatedData[AppointmentResponse]]:
    page = await bookings.list_appointments(
        pagination,
        actor=actor,
        staff_id=staff_id,
        customer_id=customer_id,
        status=appointment_status,
        appointment_date=appointment_date,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(page)


@router.get(
    "/calendar",
    summary="Appointment calendar",
    description="Bookings grouped by date for a range of at most 42 days.",
    response_model=APIResponse[CalendarResponse],
)
async def get_calendar(
    bookings: AppointmentServiceDep,
    start_date: date,
    end_date: date,
    actor: CurrentUser = Depends(_READ),
    staff_id: UUID | None = Query(default=None),
) -> APIResponse[CalendarResponse]:
    calendar = await bookings.get_calendar(
        actor=actor,
        start_date=start_date,
        end_date=end_date,
        staff_id=staff_id,
    )
    return success_response(calendar)


@router.get(
    "/{appointment_id}",
    summary="Appointment details",
    response_model=APIResponse[AppointmentResponse],
)
async def get_appointment(
    appointment_id: UUID,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_READ),
) -> APIResponse[AppointmentResponse]:
    return success_response(await bookings.get_appointment(appointment_id, actor=actor))


@router.post(
    "",
    summary="Create appointment",
    description="Book one or more services. Duration and end_time are calculated from snapshots.",
    response_model=APIResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    payload: AppointmentCreateRequest,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[AppointmentResponse]:
    created = await bookings.create_appointment(payload, actor=actor)
    return success_response(created, message="Appointment created")


@router.put(
    "/{appointment_id}",
    summary="Edit appointment",
    description="Update notes, customer, staff, or services. "
    "Terminal appointments cannot be edited.",
    response_model=APIResponse[AppointmentResponse],
)
async def update_appointment(
    appointment_id: UUID,
    payload: AppointmentUpdateRequest,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[AppointmentResponse]:
    updated = await bookings.update_appointment(appointment_id, payload, actor=actor)
    return success_response(updated, message="Appointment updated")


@router.patch(
    "/{appointment_id}/status",
    summary="Update appointment status",
    description="Advance or close the booking using the allowed status workflow.",
    response_model=APIResponse[AppointmentResponse],
)
async def change_appointment_status(
    appointment_id: UUID,
    payload: AppointmentStatusRequest,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[AppointmentResponse]:
    updated = await bookings.change_status(appointment_id, payload.status, actor=actor)
    return success_response(updated, message="Appointment status updated")


@router.patch(
    "/{appointment_id}/cancel",
    summary="Cancel appointment",
    description="Cancel a PENDING or CONFIRMED booking.",
    response_model=APIResponse[AppointmentResponse],
)
async def cancel_appointment(
    appointment_id: UUID,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[AppointmentResponse]:
    updated = await bookings.cancel_appointment(appointment_id, actor=actor)
    return success_response(updated, message="Appointment cancelled")


@router.patch(
    "/{appointment_id}/reschedule",
    summary="Reschedule appointment",
    description="Move a booking to a new date/time. Availability is re-checked.",
    response_model=APIResponse[AppointmentResponse],
)
async def reschedule_appointment(
    appointment_id: UUID,
    payload: AppointmentRescheduleRequest,
    bookings: AppointmentServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[AppointmentResponse]:
    updated = await bookings.reschedule_appointment(appointment_id, payload, actor=actor)
    return success_response(updated, message="Appointment rescheduled")
