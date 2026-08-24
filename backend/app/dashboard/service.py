from calendar import monthrange
from datetime import UTC, date, datetime, timedelta

from app.core.exceptions import ValidationException
from app.dashboard.repository import DashboardRepository
from app.dashboard.schemas import (
    AppointmentDayResponse,
    AppointmentSeriesResponse,
    DashboardOverviewResponse,
    RevenuePointResponse,
    RevenueSeriesResponse,
    TopPerformerResponse,
    TopPerformersResponse,
)

_MAX_RANGE_DAYS = 366
_GROUP_DAY = "day"
_GROUP_MONTH = "month"


def _utc_today() -> date:
    return datetime.now(UTC).date()


def _day_start(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _add_months(day: date, months: int) -> date:
    year = day.year + (day.month - 1 + months) // 12
    month = (day.month - 1 + months) % 12 + 1
    last = monthrange(year, month)[1]
    return date(year, month, min(day.day, last))


def _month_start(day: date) -> date:
    return date(day.year, day.month, 1)


def _exclusive_end(day: date) -> datetime:
    return _day_start(day) + timedelta(days=1)


class DashboardService:
    """Salon KPI aggregations. Windows are calendar dates in UTC."""

    def __init__(self, repository: DashboardRepository) -> None:
        self.repository = repository

    async def get_overview(self) -> DashboardOverviewResponse:
        today = _utc_today()
        month_start = _month_start(today)
        month_start_dt = _day_start(month_start)
        month_end_dt = _day_start(_add_months(month_start, 1))
        revenue_today, revenue_month = await self.repository.revenue_totals(
            month_start=month_start_dt,
            month_end=month_end_dt,
            today_start=_day_start(today),
            today_end=_exclusive_end(today),
        )
        appointments_today, customers_served = (
            await self.repository.today_appointment_stats(today)
        )
        average_ticket = await self.repository.average_ticket_size(
            month_start_dt,
            month_end_dt,
        )
        return DashboardOverviewResponse(
            as_of=datetime.now(UTC),
            revenue_today=revenue_today,
            revenue_this_month=revenue_month,
            appointments_today=appointments_today,
            customers_served=customers_served,
            average_ticket_size=average_ticket,
        )

    async def get_revenue_series(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        group_by: str = _GROUP_DAY,
    ) -> RevenueSeriesResponse:
        if group_by not in {_GROUP_DAY, _GROUP_MONTH}:
            raise ValidationException("group_by must be 'day' or 'month'")
        start, end = self._resolve_range(start_date, end_date)
        start_dt = _day_start(start)
        end_dt = _exclusive_end(end)
        if group_by == _GROUP_MONTH:
            rows = await self.repository.revenue_by_month(start_dt, end_dt)
            items = [
                RevenuePointResponse(period=f"{year:04d}-{month:02d}", revenue=revenue)
                for year, month, revenue in rows
            ]
        else:
            rows_day = await self.repository.revenue_by_day(start_dt, end_dt)
            items = [
                RevenuePointResponse(period=day.isoformat(), revenue=revenue)
                for day, revenue in rows_day
            ]
        return RevenueSeriesResponse(
            group_by=group_by,
            start_date=start,
            end_date=end,
            items=items,
        )

    async def get_appointment_series(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AppointmentSeriesResponse:
        start, end = self._resolve_range(start_date, end_date)
        rows = await self.repository.appointments_by_day(start, end)
        return AppointmentSeriesResponse(
            start_date=start,
            end_date=end,
            items=[
                AppointmentDayResponse(
                    appointment_date=day,
                    total=total,
                    completed=completed,
                    cancelled=cancelled,
                )
                for day, total, completed, cancelled in rows
            ],
        )

    async def get_top_performers(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 5,
    ) -> TopPerformersResponse:
        if limit < 1 or limit > 20:
            raise ValidationException("limit must be between 1 and 20")
        start, end = self._resolve_range(start_date, end_date)
        rows = await self.repository.top_performers(
            _day_start(start),
            _exclusive_end(end),
            limit=limit,
        )
        return TopPerformersResponse(
            start_date=start,
            end_date=end,
            items=[
                TopPerformerResponse(
                    staff_id=staff_id,
                    staff_name=staff_name,
                    revenue=revenue,
                    appointments_completed=completed,
                )
                for staff_id, staff_name, revenue, completed in rows
            ],
        )

    def _resolve_range(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> tuple[date, date]:
        today = _utc_today()
        end = end_date or today
        start = start_date or _month_start(end)
        if start > end:
            raise ValidationException("start_date must be on or before end_date")
        if (end - start).days > _MAX_RANGE_DAYS:
            raise ValidationException("Date range cannot exceed 366 days")
        return start, end
