from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, Numeric, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import AppointmentStatus
from app.database.base import (
    ACTIVE_ROW_SQL,
    BaseModel,
    BranchAwareModel,
    check_allowed_values,
    restrict_fk,
)

if TYPE_CHECKING:
    from app.billing.models import Invoice, Payment
    from app.commissions.models import Commission
    from app.customers.models import Customer
    from app.services.models import Service
    from app.staff.models import Staff
    from app.tips.models import Tip


class Appointment(BranchAwareModel):
    """Core booking: one customer, one staff member, many services."""

    __tablename__ = "appointments"

    customer_id: Mapped[UUID] = mapped_column(restrict_fk("customers.id"), nullable=False)
    staff_id: Mapped[UUID] = mapped_column(restrict_fk("staff.id"), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AppointmentStatus.PENDING,
        server_default=AppointmentStatus.PENDING.value,
    )
    notes: Mapped[str | None] = mapped_column(nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="appointments")
    staff: Mapped[Staff] = relationship(back_populates="appointments")
    appointment_services: Mapped[list[AppointmentService]] = relationship(
        back_populates="appointment",
        lazy="selectin",
    )
    invoice: Mapped[Invoice | None] = relationship(back_populates="appointment", uselist=False)
    payments: Mapped[list[Payment]] = relationship(back_populates="appointment", lazy="selectin")
    commission: Mapped[Commission | None] = relationship(
        back_populates="appointment",
        uselist=False,
    )
    tips: Mapped[list[Tip]] = relationship(back_populates="appointment", lazy="selectin")

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="end_after_start"),
        check_allowed_values(
            "status",
            tuple(item.value for item in AppointmentStatus),
            name="status_allowed",
        ),
        Index(
            "ix_appointments_staff_slot_active",
            "staff_id",
            "appointment_date",
            "start_time",
            "end_time",
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_appointments_date_status", "appointment_date", "status"),
        Index("ix_appointments_customer_id", "customer_id"),
        Index("ix_appointments_status", "status"),
        Index("ix_appointments_completed_at", "completed_at"),
    )


class AppointmentService(BaseModel):
    """Appointment line item with immutable price and duration snapshots."""

    __tablename__ = "appointment_services"

    appointment_id: Mapped[UUID] = mapped_column(restrict_fk("appointments.id"), nullable=False)
    service_id: Mapped[UUID] = mapped_column(restrict_fk("services.id"), nullable=False)
    service_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_minutes_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    appointment: Mapped[Appointment] = relationship(back_populates="appointment_services")
    service: Mapped[Service] = relationship(back_populates="appointment_services")

    __table_args__ = (
        CheckConstraint("duration_minutes_snapshot > 0", name="duration_minutes_snapshot_positive"),
        CheckConstraint("price_snapshot > 0", name="price_snapshot_positive"),
        Index(
            "uq_appointment_services_appointment_service_active",
            "appointment_id",
            "service_id",
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_appointment_services_appointment_id", "appointment_id"),
        Index("ix_appointment_services_service_id", "service_id"),
    )
