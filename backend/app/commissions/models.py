from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import ACTIVE_ROW_SQL, BranchAwareModel, restrict_fk

if TYPE_CHECKING:
    from app.appointments.models import Appointment
    from app.staff.models import Staff


class Commission(BranchAwareModel):
    """Permanent staff earnings snapshot. Generated once; never recalculated."""

    __tablename__ = "commissions"

    appointment_id: Mapped[UUID] = mapped_column(restrict_fk("appointments.id"), nullable=False)
    staff_id: Mapped[UUID] = mapped_column(restrict_fk("staff.id"), nullable=False)
    service_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    commission_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    appointment: Mapped[Appointment] = relationship(back_populates="commission")
    staff: Mapped[Staff] = relationship(back_populates="commissions")

    __table_args__ = (
        CheckConstraint("service_revenue > 0", name="service_revenue_positive"),
        CheckConstraint(
            "commission_percentage >= 0 AND commission_percentage <= 100",
            name="commission_percentage",
        ),
        CheckConstraint("commission_amount >= 0", name="commission_amount_non_negative"),
        Index(
            "uq_commissions_appointment_id_active",
            "appointment_id",
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_commissions_staff_id", "staff_id"),
        Index("ix_commissions_staff_created_at", "staff_id", "created_at"),
    )
