from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PaymentMethod, PaymentStatus
from app.database.base import (
    ACTIVE_ROW_SQL,
    BranchAwareModel,
    check_allowed_values,
    restrict_fk,
)

if TYPE_CHECKING:
    from app.appointments.models import Appointment


class Invoice(BranchAwareModel):
    """Financial document generated after an appointment is completed. One per appointment."""

    __tablename__ = "invoices"

    appointment_id: Mapped[UUID] = mapped_column(restrict_fk("appointments.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(40), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    appointment: Mapped[Appointment] = relationship(back_populates="invoice")

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint("tax >= 0", name="tax_non_negative"),
        CheckConstraint("total = subtotal + tax", name="total_matches_subtotal_tax"),
        CheckConstraint("total > 0", name="total_positive"),
        Index(
            "uq_invoices_appointment_id_active",
            "appointment_id",
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index(
            "uq_invoices_invoice_number_active",
            "invoice_number",
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_invoices_created_at", "created_at"),
    )


class Payment(BranchAwareModel):
    """Payment attempt or success against an appointment."""

    __tablename__ = "payments"

    appointment_id: Mapped[UUID] = mapped_column(restrict_fk("appointments.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(String(20), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    appointment: Mapped[Appointment] = relationship(back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        check_allowed_values(
            "payment_method",
            tuple(item.value for item in PaymentMethod),
            name="payment_method_allowed",
        ),
        check_allowed_values(
            "payment_status",
            tuple(item.value for item in PaymentStatus),
            name="payment_status_allowed",
        ),
        CheckConstraint(
            "(payment_status <> 'SUCCESS') OR (paid_at IS NOT NULL)",
            name="success_requires_paid_at",
        ),
        Index("ix_payments_appointment_id", "appointment_id"),
        Index("ix_payments_paid_at_status", "paid_at", "payment_status"),
        Index("ix_payments_status_created_at", "payment_status", "created_at"),
    )
