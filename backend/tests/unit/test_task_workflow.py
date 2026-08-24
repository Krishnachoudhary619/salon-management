from app.common.enums import TaskStatus
from app.tasks.workflow import can_transition


def test_task_status_moves_forward_only() -> None:
    assert can_transition(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
    assert not can_transition(TaskStatus.PENDING, TaskStatus.COMPLETED)
    assert can_transition(TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)
    assert not can_transition(TaskStatus.IN_PROGRESS, TaskStatus.PENDING)
    assert not can_transition(TaskStatus.COMPLETED, TaskStatus.PENDING)
    assert not can_transition(TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS)
