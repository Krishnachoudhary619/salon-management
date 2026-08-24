from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from app.appointments.models import Appointment
from app.billing.models import Payment
from app.commissions.models import Commission
from app.common.enums import AppointmentStatus, PaymentStatus
from app.staff.models import Staff
from app.tips.models import Tip

_MONEY = Decimal("0.01")


def _money(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(_MONEY, rounding=ROUND_HALF_UP)


def _count(value: object) -> int:
    return int(value or 0)


class PerformanceRepository:
    """SQL aggregations for staff productivity. Never loads appointment row lists."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def staff_metrics(
        self,
        *,
        start_date: date,
        end_date: date,
        start_at: datetime,
        end_at: datetime,
        staff_id: UUID | None = None,
    ) -> list[tuple[UUID, str, Decimal, int, int, Decimal, Decimal]]:
        revenue_sq = (
            select(
                Appointment.staff_id.label("staff_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("revenue"),
            )
            .select_from(Payment)
            .join(Appointment, Appointment.id == Payment.appointment_id)
            .where(
                Payment.payment_status == PaymentStatus.SUCCESS,
                Payment.is_deleted.is_(False),
                Appointment.is_deleted.is_(False),
                Payment.paid_at >= start_at,
                Payment.paid_at < end_at,
            )
            .group_by(Appointment.staff_id)
            .subquery()
        )
        appointments_sq = (
            select(
                Appointment.staff_id.label("staff_id"),
                func.count().label("appointments_completed"),
                func.count(func.distinct(Appointment.customer_id)).label("customers_served"),
            )
            .where(
                Appointment.status == AppointmentStatus.COMPLETED,
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
            )
            .group_by(Appointment.staff_id)
            .subquery()
        )
        commission_sq = (
            select(
                Commission.staff_id.label("staff_id"),
                func.coalesce(func.sum(Commission.commission_amount), 0).label(
                    "commission_earned"
                ),
            )
            .where(
                Commission.is_deleted.is_(False),
                Commission.created_at >= start_at,
                Commission.created_at < end_at,
            )
            .group_by(Commission.staff_id)
            .subquery()
        )
        tips_sq = (
            select(
                Tip.staff_id.label("staff_id"),
                func.coalesce(func.sum(Tip.amount), 0).label("tips_earned"),
            )
            .where(
                Tip.is_deleted.is_(False),
                Tip.created_at >= start_at,
                Tip.created_at < end_at,
            )
            .group_by(Tip.staff_id)
            .subquery()
        )
        filters: list[ColumnElement[bool]] = [Staff.is_deleted.is_(False)]
        if staff_id is not None:
            filters.append(Staff.id == staff_id)
        stmt = (
            select(
                Staff.id,
                Staff.name,
                func.coalesce(revenue_sq.c.revenue, 0),
                func.coalesce(appointments_sq.c.customers_served, 0),
                func.coalesce(appointments_sq.c.appointments_completed, 0),
                func.coalesce(tips_sq.c.tips_earned, 0),
                func.coalesce(commission_sq.c.commission_earned, 0),
            )
            .outerjoin(revenue_sq, revenue_sq.c.staff_id == Staff.id)
            .outerjoin(appointments_sq, appointments_sq.c.staff_id == Staff.id)
            .outerjoin(commission_sq, commission_sq.c.staff_id == Staff.id)
            .outerjoin(tips_sq, tips_sq.c.staff_id == Staff.id)
            .where(*filters)
            .order_by(func.coalesce(revenue_sq.c.revenue, 0).desc(), Staff.name.asc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            (
                row[0],
                row[1],
                _money(row[2]),
                _count(row[3]),
                _count(row[4]),
                _money(row[5]),
                _money(row[6]),
            )
            for row in rows
        ]
