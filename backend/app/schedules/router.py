from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.common.dependencies import PaginationDep
from app.common.enums import Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.schedules.dependencies import ScheduleServiceDep
from app.schedules.schemas import (
    AvailabilityResponse,
    StaffScheduleCreateRequest,
    StaffScheduleResponse,
    StaffScheduleUpdateRequest,
    WeeklyScheduleReplaceRequest,
    WeeklyScheduleResponse,
)

router = APIRouter(prefix="/staff-schedules", tags=["Schedules"])
availability_router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get(
    "",
    summary="List working hours",
    description="Paginated weekly schedule windows. Filter by staff and weekday.",
    response_model=APIResponse[PaginatedData[StaffScheduleResponse]],
)
async def list_schedules(
    pagination: PaginationDep,
    schedules: ScheduleServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_READ)),
    staff_id: UUID | None = Query(default=None),
    day_of_week: int | None = Query(default=None, ge=0, le=6),
) -> APIResponse[PaginatedData[StaffScheduleResponse]]:
    page = await schedules.list_schedules(
        pagination,
        staff_id=staff_id,
        day_of_week=day_of_week,
    )
    return success_response(page)


@router.get(
    "/weekly/{staff_id}",
    summary="Get weekly schedule",
    description="Return every working window for a staff member, ordered by day and start time.",
    response_model=APIResponse[WeeklyScheduleResponse],
)
async def get_weekly_schedule(
    staff_id: UUID,
    schedules: ScheduleServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_READ)),
) -> APIResponse[WeeklyScheduleResponse]:
    return success_response(await schedules.get_weekly_schedule(staff_id))


@router.put(
    "/weekly/{staff_id}",
    summary="Replace weekly schedule",
    description="Replace all working windows for a staff member. Empty list clears the week.",
    response_model=APIResponse[WeeklyScheduleResponse],
)
async def replace_weekly_schedule(
    staff_id: UUID,
    payload: WeeklyScheduleReplaceRequest,
    schedules: ScheduleServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_WRITE)),
) -> APIResponse[WeeklyScheduleResponse]:
    replaced = await schedules.replace_weekly_schedule(staff_id, payload, actor=actor)
    return success_response(replaced, message="Weekly schedule updated")


@router.get(
    "/{schedule_id}",
    summary="Get working window",
    response_model=APIResponse[StaffScheduleResponse],
)
async def get_schedule(
    schedule_id: UUID,
    schedules: ScheduleServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_READ)),
) -> APIResponse[StaffScheduleResponse]:
    return success_response(await schedules.get_schedule(schedule_id))


@router.post(
    "",
    summary="Create working window",
    description="Add a weekly working window. Split days are allowed; overlapping windows are not.",
    response_model=APIResponse[StaffScheduleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    payload: StaffScheduleCreateRequest,
    schedules: ScheduleServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_WRITE)),
) -> APIResponse[StaffScheduleResponse]:
    created = await schedules.create_schedule(payload, actor=actor)
    return success_response(created, message="Working hours created")


@router.put(
    "/{schedule_id}",
    summary="Update working window",
    response_model=APIResponse[StaffScheduleResponse],
)
async def update_schedule(
    schedule_id: UUID,
    payload: StaffScheduleUpdateRequest,
    schedules: ScheduleServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_WRITE)),
) -> APIResponse[StaffScheduleResponse]:
    updated = await schedules.update_schedule(schedule_id, payload, actor=actor)
    return success_response(updated, message="Working hours updated")


@router.delete(
    "/{schedule_id}",
    summary="Remove working window",
    description="Soft-delete a weekly window so it is ignored by availability.",
    response_model=APIResponse[None],
)
async def delete_schedule(
    schedule_id: UUID,
    schedules: ScheduleServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_WRITE)),
) -> APIResponse[None]:
    await schedules.delete_schedule(schedule_id, actor=actor)
    return success_response(message="Working hours removed")


@availability_router.get(
    "",
    summary="List available slots",
    description=(
        "Return bookable slots for a staff member on a date. "
        "Slots must fit a working window and avoid overlapping appointments."
    ),
    response_model=APIResponse[AvailabilityResponse],
)
async def get_availability(
    schedules: ScheduleServiceDep,
    staff_id: UUID,
    on_date: date = Query(alias="date"),
    _user: CurrentUser = Depends(require_permissions(Permission.SCHEDULE_READ)),
    duration_minutes: int | None = Query(default=None, gt=0),
    service_id: UUID | None = Query(default=None),
) -> APIResponse[AvailabilityResponse]:
    result = await schedules.get_availability(
        staff_id=staff_id,
        on_date=on_date,
        duration_minutes=duration_minutes,
        service_id=service_id,
    )
    return success_response(result)
