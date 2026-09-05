from datetime import date, datetime, time, timedelta

DEFAULT_SLOT_STEP_MINUTES = 15
END_OF_DAY_CLOSE = time(23, 59)


def _closes_at_midnight(window_end: time) -> bool:
    return window_end >= END_OF_DAY_CLOSE


def _window_close(day: date, window_start: time, window_end: time) -> datetime:
    """Map a schedule window to an exclusive close instant on the booking day."""
    if window_end <= window_start:
        return datetime.combine(day + timedelta(days=1), window_end)
    if _closes_at_midnight(window_end):
        return datetime.combine(day + timedelta(days=1), time(0, 0))
    return datetime.combine(day, window_end)


def intervals_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """True when [start_a, end_a) overlaps [start_b, end_b). Adjacent windows do not overlap."""
    return start_a < end_b and start_b < end_a


def window_covers(window_start: time, window_end: time, start: time, end: time) -> bool:
    """True when [start, end) sits fully inside [window_start, window_end)."""
    if start < window_start:
        return False
    if _closes_at_midnight(window_end):
        return end == time(0, 0) or end <= window_end
    return end <= window_end


def weekday_index(value: date) -> int:
    """Match staff_schedules.day_of_week: 0 = Monday … 6 = Sunday."""
    return value.weekday()


def generate_slots(
    windows: list[tuple[time, time]],
    busy: list[tuple[time, time]],
    duration_minutes: int,
    *,
    step_minutes: int = DEFAULT_SLOT_STEP_MINUTES,
) -> list[tuple[time, time]]:
    """Return bookable [start, end) slots that fit a working window and miss busy intervals."""
    if duration_minutes <= 0 or step_minutes <= 0:
        return []
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)
    day = date(2000, 1, 1)
    slots: list[tuple[time, time]] = []
    for window_start, window_end in sorted(windows, key=lambda window: window[0]):
        cursor = datetime.combine(day, window_start)
        window_close = _window_close(day, window_start, window_end)
        while cursor + duration <= window_close:
            slot_end = cursor + duration
            start_t = cursor.time()
            end_t = slot_end.time()
            if not any(
                intervals_overlap(start_t, end_t, busy_start, busy_end)
                for busy_start, busy_end in busy
            ):
                slots.append((start_t, end_t))
            cursor += step
    return slots
