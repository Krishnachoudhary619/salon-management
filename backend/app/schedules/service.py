from datetime import date, time
from uuid import UUID

from app.appointments.engine import AvailabilityEngine
from app.common.enums import SortOrder, StaffStatus
from app.common.pagination import PaginatedData, PaginationParams
from app.common.service import BaseService
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import CurrentUser
from app.schedules.engine import generate_slots, intervals_overlap, weekday_index
from app.schedules.models import StaffSchedule
from app.schedules.repository import ScheduleRepository
from app.schedules.schemas import (
    AvailabilityResponse,
    AvailabilitySlot,
    StaffScheduleCreateRequest,
    StaffScheduleResponse,
    StaffScheduleUpdateRequest,
    WeeklyScheduleReplaceRequest,
    WeeklyScheduleResponse,
    WeeklyWindowRequest,
)
from app.staff.models import Staff

logger = get_logger(__name__)

_ALLOWED_SORT = {"day_of_week", "start_time", "end_time", "created_at", "updated_at"}


def to_schedule_response(row: StaffSchedule) -> StaffScheduleResponse:
    return StaffScheduleResponse.model_validate(row)


class ScheduleService(BaseService[StaffSchedule]):
    """Weekly working hours and the availability engine."""

    def __init__(self, repository: ScheduleRepository) -> None:
        super().__init__(repository, resource_name="Staff schedule")
        self.schedule_repository = repository

    async def get_schedule(self, schedule_id: UUID) -> StaffScheduleResponse:
        return to_schedule_response(await self.get(schedule_id))

    async def list_schedules(
        self,
        params: PaginationParams,
        *,
        staff_id: UUID | None = None,
        day_of_week: int | None = None,
    ) -> PaginatedData[StaffScheduleResponse]:
        if params.sort_by is None:
            params.sort_by = "day_of_week"
            params.sort_order = SortOrder.ASC
        filters = []
        if staff_id is not None:
            filters.append(StaffSchedule.staff_id == staff_id)
        if day_of_week is not None:
            filters.append(StaffSchedule.day_of_week == day_of_week)
        page = await self.schedule_repository.list(
            params,
            filters=filters or None,
            allowed_sort_fields=_ALLOWED_SORT,
        )
        return PaginatedData(
            items=[to_schedule_response(item) for item in page.items],
            total=page.total,
            page=page.page,
            limit=page.limit,
        )

    async def get_weekly_schedule(self, staff_id: UUID) -> WeeklyScheduleResponse:
        await self._require_staff(staff_id)
        windows = await self.schedule_repository.list_for_staff(staff_id)
        return WeeklyScheduleResponse(
            staff_id=staff_id,
            windows=[to_schedule_response(row) for row in windows],
        )

    async def create_schedule(
        self,
        payload: StaffScheduleCreateRequest,
        *,
        actor: CurrentUser,
    ) -> StaffScheduleResponse:
        await self._require_staff(payload.staff_id)
        await self._ensure_no_overlap(
            payload.staff_id,
            payload.day_of_week,
            payload.start_time,
            payload.end_time,
        )
        created = await self.schedule_repository.create(
            StaffSchedule(
                staff_id=payload.staff_id,
                day_of_week=payload.day_of_week,
                start_time=payload.start_time,
                end_time=payload.end_time,
            ),
            created_by=actor.id,
        )
        logger.info("staff_schedule_created", schedule_id=str(created.id))
        return to_schedule_response(created)

    async def update_schedule(
        self,
        schedule_id: UUID,
        payload: StaffScheduleUpdateRequest,
        *,
        actor: CurrentUser,
    ) -> StaffScheduleResponse:
        row = await self.get(schedule_id)
        changes = payload.model_dump(exclude_unset=True)
        day_of_week = changes.get("day_of_week", row.day_of_week)
        start_time = changes.get("start_time", row.start_time)
        end_time = changes.get("end_time", row.end_time)
        if end_time <= start_time:
            raise ValidationException("end_time must be after start_time")
        await self._ensure_no_overlap(
            row.staff_id,
            day_of_week,
            start_time,
            end_time,
            exclude_id=row.id,
        )
        for field, value in changes.items():
            setattr(row, field, value)
        updated = await self.schedule_repository.update(row, updated_by=actor.id)
        logger.info("staff_schedule_updated", schedule_id=str(row.id))
        return to_schedule_response(updated)

    async def delete_schedule(self, schedule_id: UUID, *, actor: CurrentUser) -> None:
        row = await self.get(schedule_id)
        await self.schedule_repository.soft_delete(row, deleted_by=actor.id)
        logger.info("staff_schedule_deleted", schedule_id=str(schedule_id))

    async def replace_weekly_schedule(
        self,
        staff_id: UUID,
        payload: WeeklyScheduleReplaceRequest,
        *,
        actor: CurrentUser,
    ) -> WeeklyScheduleResponse:
        await self._require_staff(staff_id)
        self._ensure_payload_windows_do_not_overlap(payload.windows)
        existing = await self.schedule_repository.list_for_staff(staff_id)
        for row in existing:
            await self.schedule_repository.soft_delete(row, deleted_by=actor.id)
        for window in payload.windows:
            await self.schedule_repository.create(
                StaffSchedule(
                    staff_id=staff_id,
                    day_of_week=window.day_of_week,
                    start_time=window.start_time,
                    end_time=window.end_time,
                ),
                created_by=actor.id,
            )
        logger.info("staff_weekly_schedule_replaced", staff_id=str(staff_id))
        return await self.get_weekly_schedule(staff_id)

    async def get_availability(
        self,
        *,
        staff_id: UUID,
        on_date: date,
        duration_minutes: int | None = None,
        service_id: UUID | None = None,
    ) -> AvailabilityResponse:
        staff = await self._require_working_staff(staff_id)
        duration = await self._resolve_duration(duration_minutes, service_id)
        day = weekday_index(on_date)
        windows = await self.schedule_repository.list_for_staff(staff.id, day_of_week=day)
        busy = await self.schedule_repository.list_busy_intervals(staff.id, on_date)
        slots = generate_slots(
            [(row.start_time, row.end_time) for row in windows],
            busy,
            duration,
        )
        return AvailabilityResponse(
            staff_id=staff.id,
            date=on_date,
            duration_minutes=duration,
            slots=[AvailabilitySlot(start_time=start, end_time=end) for start, end in slots],
        )

    async def assert_slot_available(
        self,
        *,
        staff_id: UUID,
        on_date: date,
        start_time: time,
        end_time: time,
        exclude_appointment_id: UUID | None = None,
    ) -> None:
        """Write-path check used by booking. Rejects if the staff cannot take the slot."""
        await AvailabilityEngine(self.schedule_repository).validate_slot(
            staff_id=staff_id,
            on_date=on_date,
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=exclude_appointment_id,
        )

    async def _require_staff(self, staff_id: UUID) -> Staff:
        staff = await self.schedule_repository.get_staff(staff_id)
        if staff is None:
            raise NotFoundException("Staff not found")
        return staff

    async def _require_working_staff(self, staff_id: UUID) -> Staff:
        staff = await self._require_staff(staff_id)
        if staff.status != StaffStatus.ACTIVE:
            raise ConflictException("Staff is not working")
        return staff

    async def _resolve_duration(
        self,
        duration_minutes: int | None,
        service_id: UUID | None,
    ) -> int:
        if service_id is not None:
            service = await self.schedule_repository.get_service(service_id)
            if service is None:
                raise NotFoundException("Service not found")
            if not service.is_active:
                raise ConflictException("Service is not active")
            return service.duration_minutes
        if duration_minutes is None:
            raise ValidationException("duration_minutes or service_id is required")
        return duration_minutes

    async def _ensure_no_overlap(
        self,
        staff_id: UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        existing = await self.schedule_repository.list_for_staff(
            staff_id,
            day_of_week=day_of_week,
            exclude_id=exclude_id,
        )
        for row in existing:
            if intervals_overlap(start_time, end_time, row.start_time, row.end_time):
                raise ConflictException("Working hours overlap an existing window for this day")

    def _ensure_payload_windows_do_not_overlap(self, windows: list[WeeklyWindowRequest]) -> None:
        by_day: dict[int, list[WeeklyWindowRequest]] = {}
        for window in windows:
            by_day.setdefault(window.day_of_week, []).append(window)
        for day_windows in by_day.values():
            ordered = sorted(day_windows, key=lambda item: item.start_time)
            for index in range(1, len(ordered)):
                previous = ordered[index - 1]
                current = ordered[index]
                if intervals_overlap(
                    previous.start_time,
                    previous.end_time,
                    current.start_time,
                    current.end_time,
                ):
                    raise ConflictException("Working hours overlap an existing window for this day")
