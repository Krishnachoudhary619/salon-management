from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.common.enums import Permission
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.performance.dependencies import PerformanceServiceDep
from app.performance.schemas import StaffPerformanceResponse, TeamPerformanceResponse

router = APIRouter(prefix="/performance", tags=["Performance"])

_TEAM = require_permissions(Permission.PERFORMANCE_READ)
_STAFF = require_permissions(
    Permission.PERFORMANCE_READ,
    Permission.PERFORMANCE_READ_OWN,
    any_of=True,
)


@router.get(
    "/team",
    summary="Team performance",
    description="Per-staff revenue, volume, tips, and commission from SQL aggregations.",
    response_model=APIResponse[TeamPerformanceResponse],
)
async def get_team_performance(
    performance: PerformanceServiceDep,
    _user: CurrentUser = Depends(_TEAM),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> APIResponse[TeamPerformanceResponse]:
    page = await performance.get_team_performance(
        start_date=start_date,
        end_date=end_date,
    )
    return success_response(page)


@router.get(
    "/staff/{staff_id}",
    summary="Staff performance",
    description="One staff member's KPIs. Staff callers may only read their own metrics.",
    response_model=APIResponse[StaffPerformanceResponse],
)
async def get_staff_performance(
    staff_id: UUID,
    performance: PerformanceServiceDep,
    actor: CurrentUser = Depends(_STAFF),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> APIResponse[StaffPerformanceResponse]:
    detail = await performance.get_staff_performance(
        staff_id,
        actor=actor,
        start_date=start_date,
        end_date=end_date,
    )
    return success_response(detail)
