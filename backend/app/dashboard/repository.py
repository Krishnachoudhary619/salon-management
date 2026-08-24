from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.appointments.models import Appointment
from app.billing.models import Invoice, Payment
from app.common.enums import AppointmentStatus, PaymentStatus
from app.staff.models import Staff

_MONEY = Decimal("0.01")


def _money(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(_MONEY, rounding=ROUND_HALF_UP)


def _count(value: object) -> int:
    return int(value or 0)


def _as_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


class DashboardRepository:
    """SQL aggregations for dashboard cards and charts. Never loads row lists."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def revenue_totals(
        self,
        *,
        month_start: datetime,
        month_end: datetime,
        today_start: datetime,
        today_end: datetime,
    ) -> tuple[Decimal, Decimal]:
        today_amount = case(
            (
                and_(Payment.paid_at >= today_start, Payment.paid_at < today_end),
                Payment.amount,
            ),
            else_=0,
        )
        stmt = select(
            func.coalesce(func.sum(today_amount), 0),
            func.coalesce(func.sum(Payment.amount), 0),
        ).where(
            Payment.payment_status == PaymentStatus.SUCCESS,
            Payment.is_deleted.is_(False),
            Payment.paid_at >= month_start,
            Payment.paid_at < month_end,
        )
        today_total, month_total = (await self.session.execute(stmt)).one()
        return _money(today_total), _money(month_total)

    async def today_appointment_stats(self, today: date) -> tuple[int, int]:
        completed_customer = case(
            (Appointment.status == AppointmentStatus.COMPLETED, Appointment.customer_id),
        )
        stmt = select(
            func.count(),
            func.count(func.distinct(completed_customer)),
        ).where(
            Appointment.appointment_date == today,
            Appointment.is_deleted.is_(False),
        )
        appointments_today, customers_served = (await self.session.execute(stmt)).one()
        return _count(appointments_today), _count(customers_served)

    async def average_ticket_size(self, start: datetime, end: datetime) -> Decimal:
        stmt = select(func.avg(Invoice.total)).where(
            Invoice.is_deleted.is_(False),
            Invoice.created_at >= start,
            Invoice.created_at < end,
        )
        return _money((await self.session.execute(stmt)).scalar_one())

    async def revenue_by_day(
        self,
        start: datetime,
        end: datetime,
    ) -> list[tuple[date, Decimal]]:
        day = func.date(Payment.paid_at)
        stmt = (
            select(day, func.coalesce(func.sum(Payment.amount), 0))
            .where(*self._success_filters(start, end))
            .group_by(day)
            .order_by(day)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(_as_date(row[0]), _money(row[1])) for row in rows if row[0] is not None]

    async def revenue_by_month(
        self,
        start: datetime,
        end: datetime,
    ) -> list[tuple[int, int, Decimal]]:
        year = func.extract("year", Payment.paid_at)
        month = func.extract("month", Payment.paid_at)
        stmt = (
            select(year, month, func.coalesce(func.sum(Payment.amount), 0))
            .where(*self._success_filters(start, end))
            .group_by(year, month)
            .order_by(year, month)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(int(row[0]), int(row[1]), _money(row[2])) for row in rows]

    async def appointments_by_day(
        self,
        start_date: date,
        end_date: date,
    ) -> list[tuple[date, int, int, int]]:
        completed = func.coalesce(
            func.sum(case((Appointment.status == AppointmentStatus.COMPLETED, 1), else_=0)),
            0,
        )
        cancelled = func.coalesce(
            func.sum(case((Appointment.status == AppointmentStatus.CANCELLED, 1), else_=0)),
            0,
        )
        stmt = (
            select(
                Appointment.appointment_date,
                func.count(),
                completed,
                cancelled,
            )
            .where(
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
            )
            .group_by(Appointment.appointment_date)
            .order_by(Appointment.appointment_date)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            (row[0], _count(row[1]), _count(row[2]), _count(row[3])) for row in rows
        ]

    async def top_performers(
        self,
        start: datetime,
        end: datetime,
        *,
        limit: int,
    ) -> list[tuple[UUID, str, Decimal, int]]:
        revenue = func.coalesce(func.sum(Payment.amount), 0)
        stmt = (
            select(
                Appointment.staff_id,
                Staff.name,
                revenue,
                func.count(func.distinct(Appointment.id)),
            )
            .select_from(Payment)
            .join(Appointment, Appointment.id == Payment.appointment_id)
            .join(Staff, Staff.id == Appointment.staff_id)
            .where(
                Payment.payment_status == PaymentStatus.SUCCESS,
                Payment.is_deleted.is_(False),
                Appointment.is_deleted.is_(False),
                Staff.is_deleted.is_(False),
                Payment.paid_at >= start,
                Payment.paid_at < end,
            )
            .group_by(Appointment.staff_id, Staff.name)
            .order_by(revenue.desc(), Staff.name.asc())
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], row[1], _money(row[2]), _count(row[3])) for row in rows]

    def _success_filters(self, start: datetime, end: datetime) -> tuple[object, ...]:
        return (
            Payment.payment_status == PaymentStatus.SUCCESS,
            Payment.is_deleted.is_(False),
            Payment.paid_at >= start,
            Payment.paid_at < end,
        )
