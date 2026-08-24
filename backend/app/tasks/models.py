from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import TaskStatus
from app.database.base import BranchAwareModel, check_allowed_values, restrict_fk

if TYPE_CHECKING:
    from app.staff.models import Staff


class Task(BranchAwareModel):
    """Non-appointment work item assigned to staff."""

    __tablename__ = "tasks"

    assigned_staff_id: Mapped[UUID] = mapped_column(restrict_fk("staff.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.PENDING,
        server_default=TaskStatus.PENDING.value,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_staff: Mapped[Staff] = relationship(back_populates="tasks")

    __table_args__ = (
        check_allowed_values(
            "status",
            tuple(item.value for item in TaskStatus),
            name="status_allowed",
        ),
        CheckConstraint(
            "(status <> 'COMPLETED') OR (completed_at IS NOT NULL)",
            name="completed_requires_completed_at",
        ),
        Index("ix_tasks_assigned_staff_status", "assigned_staff_id", "status"),
        Index("ix_tasks_due_date", "due_date"),
    )
