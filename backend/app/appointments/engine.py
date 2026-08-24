from datetime import date, time
from uuid import UUID

from app.appointments.duration import add_minutes, minutes_between
from app.common.enums import StaffStatus
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.schedules.engine import generate_slots, intervals_overlap, weekday_index, window_covers
from app.schedules.repository import ScheduleRepository


def _normalize(value: time) -> time:
    return value.replace(microsecond=0)


class AvailabilityEngine:
    """Write-path booking checks. Failures are rejected before an appointment is stored."""

    def __init__(self, repository: ScheduleRepository) -> None:
        self.repository = repository

    async def validate_slot(
        self,
        *,
        staff_id: UUID,
        on_date: date,
        start_time: time,
        end_time: time,
        duration_minutes: int | None = None,
        exclude_appointment_id: UUID | None = None,
    ) -> None:
        start_time = _normalize(start_time)
        end_time = _normalize(end_time)
        duration = self._resolve_duration(start_time, end_time, duration_minutes)

        staff = await self.repository.get_staff(staff_id)
        if staff is None:
            raise NotFoundException("Staff not found")
        if staff.status != StaffStatus.ACTIVE:
            raise ConflictException("Staff is not working")

        windows = await self.repository.list_for_staff(
            staff.id,
            day_of_week=weekday_index(on_date),
        )
        window_times = [(_normalize(row.start_time), _normalize(row.end_time)) for row in windows]
        if not window_times:
            raise ConflictException("Staff is not working on this day")

        if not any(
            window_covers(window_start, window_end, start_time, end_time)
            for window_start, window_end in window_times
        ):
            raise ConflictException("Appointment duration does not fit the working schedule")

        busy = [
            (_normalize(busy_start), _normalize(busy_end))
            for busy_start, busy_end in await self.repository.list_busy_intervals(
                staff.id,
                on_date,
                exclude_appointment_id=exclude_appointment_id,
            )
        ]
        if any(
            intervals_overlap(start_time, end_time, busy_start, busy_end)
            for busy_start, busy_end in busy
        ):
            raise ConflictException("This time slot overlaps an existing appointment")

        open_slots = {
            (_normalize(slot_start), _normalize(slot_end))
            for slot_start, slot_end in generate_slots(window_times, busy, duration)
        }
        if (start_time, end_time) not in open_slots:
            raise ConflictException("This time slot is not available")

    def _resolve_duration(
        self,
        start_time: time,
        end_time: time,
        duration_minutes: int | None,
    ) -> int:
        try:
            computed = minutes_between(start_time, end_time)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        if duration_minutes is None:
            return computed
        if duration_minutes <= 0:
            raise ValidationException("Duration must be greater than zero")
        try:
            expected_end = add_minutes(start_time, duration_minutes)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        if _normalize(expected_end) != end_time:
            raise ValidationException("end_time must equal start_time plus service duration")
        return duration_minutes
