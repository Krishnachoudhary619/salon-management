from app.common.enums import AppointmentStatus

ALLOWED_TRANSITIONS: dict[AppointmentStatus, frozenset[AppointmentStatus]] = {
    AppointmentStatus.PENDING: frozenset(
        {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED}
    ),
    AppointmentStatus.CONFIRMED: frozenset(
        {
            AppointmentStatus.ARRIVED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        }
    ),
    AppointmentStatus.ARRIVED: frozenset({AppointmentStatus.IN_PROGRESS}),
    AppointmentStatus.IN_PROGRESS: frozenset({AppointmentStatus.COMPLETED}),
    AppointmentStatus.COMPLETED: frozenset(),
    AppointmentStatus.CANCELLED: frozenset(),
    AppointmentStatus.NO_SHOW: frozenset(),
}

TERMINAL_STATUSES = frozenset(
    {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    }
)

RESCHEDULABLE_STATUSES = frozenset(
    {
        AppointmentStatus.PENDING,
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.ARRIVED,
        AppointmentStatus.IN_PROGRESS,
    }
)


def as_status(value: AppointmentStatus | str) -> AppointmentStatus:
    return AppointmentStatus(value)


def can_transition(current: AppointmentStatus | str, target: AppointmentStatus | str) -> bool:
    current_status = as_status(current)
    target_status = as_status(target)
    return target_status in ALLOWED_TRANSITIONS.get(current_status, frozenset())
