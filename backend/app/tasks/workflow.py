from app.common.enums import TaskStatus

ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.PENDING: frozenset({TaskStatus.IN_PROGRESS}),
    TaskStatus.IN_PROGRESS: frozenset({TaskStatus.COMPLETED}),
    TaskStatus.COMPLETED: frozenset(),
}


def as_status(value: TaskStatus | str) -> TaskStatus:
    return TaskStatus(value)


def can_transition(current: TaskStatus | str, target: TaskStatus | str) -> bool:
    current_status = as_status(current)
    target_status = as_status(target)
    return target_status in ALLOWED_TRANSITIONS.get(current_status, frozenset())
