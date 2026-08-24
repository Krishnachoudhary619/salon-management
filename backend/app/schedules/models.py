from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, SmallInteger, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import ACTIVE_ROW_SQL, BranchAwareModel, restrict_fk

if TYPE_CHECKING:
    from app.staff.models import Staff


class StaffSchedule(BranchAwareModel):
    """Weekly working window used by the availability engine."""

    __tablename__ = "staff_schedules"

    staff_id: Mapped[UUID] = mapped_column(restrict_fk("staff.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    staff: Mapped[Staff] = relationship(back_populates="schedules")

    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="day_of_week_range"),
        CheckConstraint("end_time > start_time", name="end_after_start"),
        Index(
            "ix_staff_schedules_staff_day_active",
            "staff_id",
            "day_of_week",
            postgresql_where=ACTIVE_ROW_SQL,
        ),
    )
