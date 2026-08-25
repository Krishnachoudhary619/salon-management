from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.appointments.dependencies import AppointmentServiceDep
from app.appointments.schemas import AppointmentCreateRequest, AppointmentResponse
from app.common.enums import Role, SortOrder, StaffStatus
from app.common.pagination import PaginationParams
from app.common.responses import APIResponse, success_response
from app.core.security import CurrentUser
from app.customers.schemas import CustomerCreateRequest
from app.public.schemas import (
    PublicBookingRequest,
    PublicCatalogResponse,
    PublicServiceItem,
    PublicStaffItem,
)
from app.schedules.dependencies import ScheduleServiceDep
from app.schedules.schemas import AvailabilityResponse
from app.services.dependencies import ServiceServiceDep
from app.staff.dependencies import StaffServiceDep

router = APIRouter(prefix="/public", tags=["Public booking"])

_PUBLIC_ACTOR = CurrentUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    roles=[Role.ADMIN],
    email="reservations@system",
)


@router.get(
    "/catalog",
    summary="Public booking catalog",
    description="Active services and staff for the website reservation form.",
    response_model=APIResponse[PublicCatalogResponse],
)
async def get_public_catalog(
    catalog: ServiceServiceDep,
    roster: StaffServiceDep,
) -> APIResponse[PublicCatalogResponse]:
    services_page = await catalog.list_services(
        PaginationParams(page=1, limit=100, sort_by="name", sort_order=SortOrder.ASC),
        is_active=True,
    )
    staff_page = await roster.list_staff(
        PaginationParams(page=1, limit=100, sort_by="name", sort_order=SortOrder.ASC),
        status=StaffStatus.ACTIVE,
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
            staff=[
                PublicStaffItem(id=item.id, name=item.name, designation=item.designation)
                for item in staff_page.items
            ],
        )
    )


@router.get(
    "/availability",
    summary="Public availability",
    description="Open slots for a staff member and service duration.",
    response_model=APIResponse[AvailabilityResponse],
)
async def get_public_availability(
    schedules: ScheduleServiceDep,
    staff_id: UUID,
    on_date: date = Query(alias="date"),
    duration_minutes: int = Query(gt=0),
) -> APIResponse[AvailabilityResponse]:
    result = await schedules.get_availability(
        staff_id=staff_id,
        on_date=on_date,
        duration_minutes=duration_minutes,
    )
    return success_response(result)


@router.post(
    "/bookings",
    summary="Public appointment booking",
    description="Create a pending appointment from the website. Customer is matched by phone.",
    response_model=APIResponse[AppointmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_public_booking(
    payload: PublicBookingRequest,
    bookings: AppointmentServiceDep,
) -> APIResponse[AppointmentResponse]:
    created = await bookings.create_appointment(
        AppointmentCreateRequest(
            customer=CustomerCreateRequest(name=payload.name, phone=payload.phone),
            staff_id=payload.staff_id,
            appointment_date=payload.appointment_date,
            start_time=payload.start_time,
            service_ids=[payload.service_id],
            notes=payload.notes,
        ),
        actor=_PUBLIC_ACTOR,
    )
    return success_response(created, message="Appointment requested")
