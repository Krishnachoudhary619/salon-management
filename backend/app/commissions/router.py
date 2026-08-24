from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.commissions.dependencies import CommissionServiceDep
from app.commissions.schemas import CommissionResponse
from app.common.dependencies import PaginationDep
from app.common.enums import Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser

router = APIRouter(prefix="/commissions", tags=["Commissions"])

_READ = require_permissions(
    Permission.COMMISSION_READ,
    Permission.COMMISSION_READ_OWN,
    any_of=True,
)


@router.get(
    "",
    summary="List commissions",
    description="Paginated historical commissions. Staff callers only see their own earnings.",
    response_model=APIResponse[PaginatedData[CommissionResponse]],
)
async def list_commissions(
    pagination: PaginationDep,
    commissions: CommissionServiceDep,
    actor: CurrentUser = Depends(_READ),
    staff_id: UUID | None = Query(default=None),
    appointment_id: UUID | None = Query(default=None),
) -> APIResponse[PaginatedData[CommissionResponse]]:
    page = await commissions.list_commissions(
        pagination,
        actor=actor,
        staff_id=staff_id,
        appointment_id=appointment_id,
    )
    return success_response(page)


@router.get(
    "/staff/{staff_id}",
    summary="Staff commissions",
    description="Historical commissions for one staff member. Amounts are never recalculated.",
    response_model=APIResponse[PaginatedData[CommissionResponse]],
)
async def list_staff_commissions(
    staff_id: UUID,
    pagination: PaginationDep,
    commissions: CommissionServiceDep,
    actor: CurrentUser = Depends(_READ),
) -> APIResponse[PaginatedData[CommissionResponse]]:
    page = await commissions.list_staff_commissions(staff_id, pagination, actor=actor)
    return success_response(page)


@router.get(
    "/{commission_id}",
    summary="Get commission",
    description="Retrieve a stored commission snapshot. Historical rates are not updated.",
    response_model=APIResponse[CommissionResponse],
)
async def get_commission(
    commission_id: UUID,
    commissions: CommissionServiceDep,
    actor: CurrentUser = Depends(_READ),
) -> APIResponse[CommissionResponse]:
    return success_response(await commissions.get_commission(commission_id, actor=actor))
