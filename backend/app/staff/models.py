from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import StaffStatus
from app.database.base import (
    ACTIVE_ROW_SQL,
    BranchAwareModel,
    check_allowed_values,
    restrict_fk,
)

if TYPE_CHECKING:
    from app.appointments.models import Appointment
    from app.commissions.models import Commission
    from app.schedules.models import StaffSchedule
    from app.tasks.models import Task
    from app.tips.models import Tip
    from app.users.models import User


class Staff(BranchAwareModel):
    """Salon employee linked to a user account."""

    __tablename__ = "staff"

    user_id: Mapped[UUID] = mapped_column(restrict_fk("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    designation: Mapped[str] = mapped_column(String(80), nullable=False)
    commission_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StaffStatus] = mapped_column(
        String(20),
        nullable=False,
        default=StaffStatus.ACTIVE,
        server_default=StaffStatus.ACTIVE.value,
    )

    user: Mapped[User] = relationship(back_populates="staff")
    schedules: Mapped[list[StaffSchedule]] = relationship(back_populates="staff", lazy="selectin")
    appointments: Mapped[list[Appointment]] = relationship(back_populates="staff", lazy="selectin")
    commissions: Mapped[list[Commission]] = relationship(back_populates="staff", lazy="selectin")
    tips: Mapped[list[Tip]] = relationship(back_populates="staff", lazy="selectin")
    tasks: Mapped[list[Task]] = relationship(back_populates="assigned_staff", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "commission_percentage >= 0 AND commission_percentage <= 100",
            name="commission_percentage",
        ),
        check_allowed_values(
            "status",
            tuple(item.value for item in StaffStatus),
            name="status_allowed",
        ),
        Index("uq_staff_user_id_active", "user_id", unique=True, postgresql_where=ACTIVE_ROW_SQL),
        Index("uq_staff_phone_active", "phone", unique=True, postgresql_where=ACTIVE_ROW_SQL),
        Index("ix_staff_status", "status"),
        Index("ix_staff_name", "name"),
    )
