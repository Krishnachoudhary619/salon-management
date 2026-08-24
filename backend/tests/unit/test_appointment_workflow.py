from datetime import time

import pytest

from app.appointments.duration import add_minutes, minutes_between
from app.appointments.workflow import can_transition
from app.common.enums import AppointmentStatus


def test_add_minutes_same_day() -> None:
    assert add_minutes(time(10, 0), 90) == time(11, 30)


def test_add_minutes_rejects_overnight() -> None:
    with pytest.raises(ValueError, match="midnight"):
        add_minutes(time(23, 30), 60)


def test_minutes_between() -> None:
    assert minutes_between(time(10, 0), time(10, 50)) == 50


def test_status_workflow() -> None:
    assert can_transition(AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)
    assert can_transition(AppointmentStatus.PENDING, AppointmentStatus.CANCELLED)
    assert not can_transition(AppointmentStatus.PENDING, AppointmentStatus.COMPLETED)
    assert can_transition(AppointmentStatus.CONFIRMED, AppointmentStatus.ARRIVED)
    assert can_transition(AppointmentStatus.CONFIRMED, AppointmentStatus.NO_SHOW)
    assert not can_transition(AppointmentStatus.ARRIVED, AppointmentStatus.CANCELLED)
    assert not can_transition(AppointmentStatus.IN_PROGRESS, AppointmentStatus.CANCELLED)
    assert can_transition(AppointmentStatus.ARRIVED, AppointmentStatus.IN_PROGRESS)
    assert can_transition(AppointmentStatus.IN_PROGRESS, AppointmentStatus.COMPLETED)
    assert not can_transition(AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED)
