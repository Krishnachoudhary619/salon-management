from datetime import date, datetime, time, timedelta


def add_minutes(start: time, minutes: int) -> time:
    """Add minutes to a local time. Overnight results are rejected."""
    if minutes <= 0:
        raise ValueError("Duration must be greater than zero")
    start_dt = datetime.combine(date(2000, 1, 1), start)
    end_dt = start_dt + timedelta(minutes=minutes)
    if end_dt.date() != start_dt.date():
        raise ValueError("Appointment cannot extend past midnight")
    return end_dt.time()


def minutes_between(start: time, end: time) -> int:
    """Whole minutes in [start, end). Overnight ranges are rejected."""
    start_dt = datetime.combine(date(2000, 1, 1), start.replace(microsecond=0))
    end_dt = datetime.combine(date(2000, 1, 1), end.replace(microsecond=0))
    delta = int((end_dt - start_dt).total_seconds() // 60)
    if delta <= 0:
        raise ValueError("end_time must be after start_time")
    return delta
