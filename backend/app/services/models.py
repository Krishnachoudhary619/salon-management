from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Uuid,
    cast,
    column,
    func,
    literal,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import ACTIVE_ROW_SQL, BranchAwareModel

if TYPE_CHECKING:
    from app.appointments.models import AppointmentService

_UNSCOPED_BRANCH_ID = UUID("00000000-0000-0000-0000-000000000000")


class Service(BranchAwareModel):
    """Bookable salon catalog item."""

    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    appointment_services: Mapped[list[AppointmentService]] = relationship(
        back_populates="service",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="duration_minutes_positive"),
        CheckConstraint("price > 0", name="price_positive"),
        Index(
            "uq_services_name_branch_active",
            func.lower(name),
            func.coalesce(column("branch_id"), cast(literal(str(_UNSCOPED_BRANCH_ID)), Uuid())),
            unique=True,
            postgresql_where=ACTIVE_ROW_SQL,
        ),
        Index("ix_services_category_is_active", "category", "is_active"),
    )
