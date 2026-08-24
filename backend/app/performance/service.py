from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.common.enums import Permission
from app.core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from app.core.permissions import has_permission
from app.core.security import CurrentUser
from app.performance.repository import PerformanceRepository
from app.performance.schemas import (
    StaffMetricsResponse,
    StaffPerformanceResponse,
    TeamPerformanceResponse,
)
from app.staff.repository import StaffRepository

_MAX_RANGE_DAYS = 366


def _utc_today() -> date:
    return datetime.now(UTC).date()


def _day_start(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=UTC)


def _month_start(day: date) -> date:
    return date(day.year, day.month, 1)


def _exclusive_end(day: date) -> datetime:
    return _day_start(day) + timedelta(days=1)


class PerformanceService:
    """Staff productivity KPIs from SQL aggregations. Windows are UTC calendar dates."""

    def __init__(
        self,
        repository: PerformanceRepository,
        *,
        staff_repository: StaffRepository,
    ) -> None:
        self.repository = repository
        self.staff_repository = staff_repository

    async def get_team_performance(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> TeamPerformanceResponse:
        start, end = self._resolve_range(start_date, end_date)
        rows = await self.repository.staff_metrics(
            start_date=start,
            end_date=end,
            start_at=_day_start(start),
            end_at=_exclusive_end(end),
        )
        return TeamPerformanceResponse(
            start_date=start,
            end_date=end,
            items=[self._to_metrics(row) for row in rows],
        )

    async def get_staff_performance(
        self,
        staff_id: UUID,
        *,
        actor: CurrentUser,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> StaffPerformanceResponse:
        await self._ensure_can_access(staff_id, actor)
        start, end = self._resolve_range(start_date, end_date)
        rows = await self.repository.staff_metrics(
            start_date=start,
            end_date=end,
            start_at=_day_start(start),
            end_at=_exclusive_end(end),
            staff_id=staff_id,
        )
        if not rows:
            raise NotFoundException("Staff not found")
        metrics = self._to_metrics(rows[0])
        return StaffPerformanceResponse(
            start_date=start,
            end_date=end,
            **metrics.model_dump(),
        )

    async def _ensure_can_access(self, staff_id: UUID, actor: CurrentUser) -> None:
        if has_permission(actor, Permission.PERFORMANCE_READ):
            return
        profile = await self.staff_repository.get_by_user_id(actor.id)
        if profile is None:
            raise PermissionDeniedException("No staff profile is linked to this account")
        if profile.id != staff_id:
            raise PermissionDeniedException("You can only access your own performance")

    def _to_metrics(
        self,
        row: tuple[UUID, str, Decimal, int, int, Decimal, Decimal],
    ) -> StaffMetricsResponse:
        staff_id, name, revenue, customers, completed, tips, commission = row
        return StaffMetricsResponse(
            staff_id=staff_id,
            staff_name=name,
            revenue_generated=revenue,
            customers_served=customers,
            appointments_completed=completed,
            tips_earned=tips,
            commission_earned=commission,
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
