from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.common.dependencies import PaginationDep
from app.common.enums import Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.tips.dependencies import TipServiceDep
from app.tips.schemas import TipCreateRequest, TipResponse, TipUpdateRequest

router = APIRouter(prefix="/tips", tags=["Tips"])

_READ = require_permissions(Permission.TIP_READ, Permission.TIP_READ_OWN, any_of=True)
_WRITE = require_permissions(Permission.TIP_WRITE)


@router.get(
    "",
    summary="List tips",
    description="Paginated discretionary tips. Separate from commission. Staff see only their own.",
    response_model=APIResponse[PaginatedData[TipResponse]],
)
async def list_tips(
    pagination: PaginationDep,
    tips: TipServiceDep,
    actor: CurrentUser = Depends(_READ),
    staff_id: UUID | None = Query(default=None),
    appointment_id: UUID | None = Query(default=None),
) -> APIResponse[PaginatedData[TipResponse]]:
    page = await tips.list_tips(
        pagination,
        actor=actor,
        staff_id=staff_id,
        appointment_id=appointment_id,
    )
    return success_response(page)


@router.post(
    "",
    summary="Add tip",
    description="Record a discretionary tip for the appointment staff. Not part of commission.",
    response_model=APIResponse[TipResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_tip(
    payload: TipCreateRequest,
    tips: TipServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[TipResponse]:
    created = await tips.create_tip(payload, actor=actor)
    return success_response(created, message="Tip recorded")


@router.get(
    "/staff/{staff_id}",
    summary="Staff tips",
    description="Tips earned by one staff member. Amounts are not added to commission.",
    response_model=APIResponse[PaginatedData[TipResponse]],
)
async def list_staff_tips(
    staff_id: UUID,
    pagination: PaginationDep,
    tips: TipServiceDep,
    actor: CurrentUser = Depends(_READ),
) -> APIResponse[PaginatedData[TipResponse]]:
    page = await tips.list_staff_tips(staff_id, pagination, actor=actor)
    return success_response(page)


@router.get(
    "/{tip_id}",
    summary="Get tip",
    description="Retrieve a stored tip. Historical commission rows are not affected.",
    response_model=APIResponse[TipResponse],
)
async def get_tip(
    tip_id: UUID,
    tips: TipServiceDep,
    actor: CurrentUser = Depends(_READ),
) -> APIResponse[TipResponse]:
    return success_response(await tips.get_tip(tip_id, actor=actor))


@router.put(
    "/{tip_id}",
    summary="Edit tip",
    description="Update tip amount or notes. Does not recalculate commission.",
    response_model=APIResponse[TipResponse],
)
async def update_tip(
    tip_id: UUID,
    payload: TipUpdateRequest,
    tips: TipServiceDep,
    actor: CurrentUser = Depends(_WRITE),
) -> APIResponse[TipResponse]:
    updated = await tips.update_tip(tip_id, payload, actor=actor)
    return success_response(updated, message="Tip updated")
