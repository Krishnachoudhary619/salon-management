from datetime import date, datetime, time, timedelta

DEFAULT_SLOT_STEP_MINUTES = 15


def intervals_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """True when [start_a, end_a) overlaps [start_b, end_b). Adjacent windows do not overlap."""
    return start_a < end_b and start_b < end_a


def window_covers(window_start: time, window_end: time, start: time, end: time) -> bool:
    """True when [start, end) sits fully inside [window_start, window_end)."""
    return window_start <= start and end <= window_end


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
        window_close = datetime.combine(day, window_end)
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
