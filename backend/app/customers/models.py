from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import ACTIVE_ROW_SQL, BranchAwareModel

if TYPE_CHECKING:
    from app.appointments.models import Appointment


class Customer(BranchAwareModel):
    """CRM guest identity. Auto-created during booking when the phone is new."""

    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    visit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    total_spent: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    last_visit: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    appointments: Mapped[list[Appointment]] = relationship(
        back_populates="customer",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("visit_count >= 0", name="visit_count_non_negative"),
        CheckConstraint("total_spent >= 0", name="total_spent_non_negative"),
        Index("uq_customers_phone_active", "phone", unique=True, postgresql_where=ACTIVE_ROW_SQL),
        Index(
            "uq_customers_email_active",
            func.lower(email),
            unique=True,
            postgresql_where=text("email IS NOT NULL AND is_deleted = false"),
        ),
        Index("ix_customers_name", "name"),
        Index("ix_customers_last_visit", "last_visit"),
    )
