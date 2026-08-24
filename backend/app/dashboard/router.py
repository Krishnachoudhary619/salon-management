from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.common.enums import Permission
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.dashboard.dependencies import DashboardServiceDep
from app.dashboard.schemas import (
    AppointmentSeriesResponse,
    DashboardOverviewResponse,
    RevenueSeriesResponse,
    TopPerformersResponse,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

_READ = require_permissions(Permission.DASHBOARD_READ)


@router.get(
    "/overview",
    summary="Dashboard overview",
    description="Today and month KPIs from SQL aggregates: revenue, volume, ticket size.",
    response_model=APIResponse[DashboardOverviewResponse],
)
async def get_overview(
    dashboard: DashboardServiceDep,
    _user: CurrentUser = Depends(_READ),
) -> APIResponse[DashboardOverviewResponse]:
    return success_response(await dashboard.get_overview())


@router.get(
    "/revenue",
    summary="Revenue series",
    description="Successful payment totals grouped by day or month. SQL aggregation only.",
    response_model=APIResponse[RevenueSeriesResponse],
)
async def get_revenue(
    dashboard: DashboardServiceDep,
    _user: CurrentUser = Depends(_READ),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    group_by: Literal["day", "month"] = Query(default="day"),
) -> APIResponse[RevenueSeriesResponse]:
    series = await dashboard.get_revenue_series(
        start_date=start_date,
        end_date=end_date,
        group_by=group_by,
    )
    return success_response(series)


@router.get(
    "/appointments",
    summary="Appointment volume",
    description="Appointment counts by date from SQL GROUP BY. Includes completed and cancelled.",
    response_model=APIResponse[AppointmentSeriesResponse],
)
async def get_appointments(
    dashboard: DashboardServiceDep,
    _user: CurrentUser = Depends(_READ),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> APIResponse[AppointmentSeriesResponse]:
    series = await dashboard.get_appointment_series(
        start_date=start_date,
        end_date=end_date,
    )
    return success_response(series)


@router.get(
    "/top-performers",
    summary="Top staff by revenue",
    description="Staff ranked by successful payment revenue. Aggregated in SQL, not in memory.",
    response_model=APIResponse[TopPerformersResponse],
)
async def get_top_performers(
    dashboard: DashboardServiceDep,
    _user: CurrentUser = Depends(_READ),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=20),
) -> APIResponse[TopPerformersResponse]:
    ranked = await dashboard.get_top_performers(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return success_response(ranked)
