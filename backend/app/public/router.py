from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.appointments.dependencies import AppointmentServiceDep
from app.appointments.schemas import AppointmentCreateRequest, AppointmentResponse
from app.common.enums import Role, SortOrder, StaffStatus
from app.common.pagination import PaginationParams
from app.common.responses import APIResponse, success_response
from app.core.exceptions import ConflictException
from app.core.security import CurrentUser
from app.customers.schemas import CustomerCreateRequest
from app.public.schemas import (
    PublicAvailabilityResponse,
    PublicBookingRequest,
    PublicCatalogResponse,
    PublicServiceItem,
)
from app.schedules.dependencies import ScheduleServiceDep
from app.schedules.schemas import AvailabilitySlot
from app.schedules.service import ScheduleService
from app.services.dependencies import ServiceServiceDep
from app.staff.dependencies import StaffServiceDep
from app.staff.schemas import StaffResponse
from app.staff.service import StaffService

router = APIRouter(prefix="/public", tags=["Public booking"])

_PUBLIC_ACTOR = CurrentUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    roles=[Role.ADMIN],
    email="reservations@system",
)


async def _active_staff(roster: StaffService) -> list[StaffResponse]:
    page = await roster.list_staff(
        PaginationParams(page=1, limit=100, sort_by="name", sort_order=SortOrder.ASC),
        status=StaffStatus.ACTIVE,
    )
    return page.items


async def _first_available_staff(
    schedules: ScheduleService,
    staff_members: list[StaffResponse],
    *,
    on_date: date,
    start_time: time,
    duration_minutes: int,
) -> UUID:
    wanted = start_time.replace(microsecond=0)
    for member in staff_members:
        availability = await schedules.get_availability(
            staff_id=member.id,
            on_date=on_date,
            duration_minutes=duration_minutes,
        )
        if any(slot.start_time.replace(microsecond=0) == wanted for slot in availability.slots):
            return member.id
    raise ConflictException("That time is no longer available. Please choose another slot.")


@router.get(
    "/catalog",
    summary="Public booking catalog",
    description="Active services for the website reservation form.",
    response_model=APIResponse[PublicCatalogResponse],
)
async def get_public_catalog(
    catalog: ServiceServiceDep,
) -> APIResponse[PublicCatalogResponse]:
    services_page = await catalog.list_services(
        PaginationParams(page=1, limit=100, sort_by="name", sort_order=SortOrder.ASC),
        is_active=True,
    )
    return success_response(
        PublicCatalogResponse(
            services=[
                PublicServiceItem(
                    id=item.id,
                    name=item.name,
                    duration_minutes=item.duration_minutes,
                    price=str(item.price),
                    category=item.category,
                )
                for item in services_page.items
            ],
        )
    )


@router.get(
    "/availability",
    summary="Public availability",
    description="Open times across all working staff for a service duration.",
    response_model=APIResponse[PublicAvailabilityResponse],
)
async def get_public_availability(
    schedules: ScheduleServiceDep,
    roster: StaffServiceDep,
    on_date: date = Query(alias="date"),
    duration_minutes: int = Query(gt=0),
) -> APIResponse[PublicAvailabilityResponse]:
    unique: dict[time, AvailabilitySlot] = {}
    for member in await _active_staff(roster):
        result = await schedules.get_availability(
            staff_id=member.id,
            on_date=on_date,
            duration_minutes=duration_minutes,
        )
        for slot in result.slots:
            unique.setdefault(slot.start_time.replace(microsecond=0), slot)
    return success_response(
        PublicAvailabilityResponse(
            date=on_date,
            duration_minutes=duration_minutes,
            slots=sorted(unique.values(), key=lambda slot: slot.start_time),
        )
    )


@router.post(
    "/bookings",
    summary="Public appointment booking",
    description="Create a pending appointment from the website. A free stylist is assigned automatically.",
    response_model=APIResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_public_booking(
    payload: PublicBookingRequest,
    bookings: AppointmentServiceDep,
    catalog: ServiceServiceDep,
    schedules: ScheduleServiceDep,
    roster: StaffServiceDep,
) -> APIResponse[AppointmentResponse]:
    service = await catalog.get(payload.service_id)
    if not service.is_active:
        raise ConflictException("Service is not active")
    staff_id = await _first_available_staff(
        schedules,
        await _active_staff(roster),
        on_date=payload.appointment_date,
        start_time=payload.start_time,
        duration_minutes=service.duration_minutes,
    )
    created = await bookings.create_appointment(
        AppointmentCreateRequest(
            customer=CustomerCreateRequest(name=payload.name, phone=payload.phone),
            staff_id=staff_id,
            appointment_date=payload.appointment_date,
            start_time=payload.start_time,
            service_ids=[payload.service_id],
            notes=payload.notes,
        ),
        actor=_PUBLIC_ACTOR,
    )
    return success_response(created, message="Appointment requested")
