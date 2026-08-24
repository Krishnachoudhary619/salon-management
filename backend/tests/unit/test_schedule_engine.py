from datetime import date, time

from app.schedules.engine import generate_slots, intervals_overlap, weekday_index, window_covers


def test_adjacent_windows_do_not_overlap() -> None:
    assert not intervals_overlap(time(10, 0), time(13, 0), time(13, 0), time(19, 0))
    assert intervals_overlap(time(10, 0), time(13, 0), time(12, 0), time(14, 0))


def test_window_covers_full_slot() -> None:
    assert window_covers(time(9, 0), time(18, 0), time(10, 0), time(11, 0))
    assert window_covers(time(9, 0), time(18, 0), time(17, 0), time(18, 0))
    assert not window_covers(time(9, 0), time(18, 0), time(8, 0), time(10, 0))
    assert not window_covers(time(9, 0), time(18, 0), time(17, 30), time(18, 30))


def test_weekday_index_monday_is_zero() -> None:
    assert weekday_index(date(2026, 8, 24)) == 0  # Monday


def test_generate_slots_steps_and_skips_busy() -> None:
    windows = [(time(10, 0), time(12, 0))]
    slots = generate_slots(windows, busy=[], duration_minutes=30, step_minutes=15)
    starts = [start.strftime("%H:%M") for start, _end in slots]
    assert starts == ["10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30"]

    free = generate_slots(
        windows,
        busy=[(time(10, 30), time(11, 0))],
        duration_minutes=30,
        step_minutes=15,
    )
    free_starts = [start.strftime("%H:%M") for start, _end in free]
    assert "10:15" not in free_starts
    assert "10:30" not in free_starts
    assert "10:00" in free_starts
    assert "11:00" in free_starts


def test_slot_must_fit_duration() -> None:
    slots = generate_slots([(time(10, 0), time(11, 0))], busy=[], duration_minutes=90)
    assert slots == []
