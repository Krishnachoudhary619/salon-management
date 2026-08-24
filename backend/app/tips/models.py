from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BranchAwareModel, restrict_fk

if TYPE_CHECKING:
    from app.appointments.models import Appointment
    from app.staff.models import Staff


class Tip(BranchAwareModel):
    """Discretionary tip, stored separately from commission."""

    __tablename__ = "tips"

    appointment_id: Mapped[UUID] = mapped_column(restrict_fk("appointments.id"), nullable=False)
    staff_id: Mapped[UUID] = mapped_column(restrict_fk("staff.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(nullable=True)

    appointment: Mapped[Appointment] = relationship(back_populates="tips")
    staff: Mapped[Staff] = relationship(back_populates="tips")

    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_tips_appointment_id", "appointment_id"),
        Index("ix_tips_staff_id", "staff_id"),
        Index("ix_tips_staff_created_at", "staff_id", "created_at"),
    )
