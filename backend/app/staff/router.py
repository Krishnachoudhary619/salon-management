from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.common.dependencies import PaginationDep
from app.common.enums import Permission, StaffStatus
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.staff.dependencies import StaffServiceDep
from app.staff.schemas import StaffCreateRequest, StaffResponse, StaffUpdateRequest

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get(
    "",
    summary="List staff",
    description="Paginated staff roster. Search name, phone, and designation.",
    response_model=APIResponse[PaginatedData[StaffResponse]],
)
async def list_staff(
    pagination: PaginationDep,
    service: StaffServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.STAFF_READ)),
    staff_status: StaffStatus | None = Query(default=None, alias="status"),
) -> APIResponse[PaginatedData[StaffResponse]]:
    page = await service.list_staff(pagination, status=staff_status)
    return success_response(page)


@router.get(
    "/{staff_id}",
    summary="View staff",
    description="Return a single staff profile.",
    response_model=APIResponse[StaffResponse],
)
async def get_staff(
    staff_id: UUID,
    service: StaffServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.STAFF_READ)),
) -> APIResponse[StaffResponse]:
    return success_response(await service.get_staff(staff_id))


@router.post(
    "",
    summary="Create staff",
    description="Create a staff profile and linked STAFF user account.",
    response_model=APIResponse[StaffResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_staff(
    payload: StaffCreateRequest,
    service: StaffServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.STAFF_WRITE)),
) -> APIResponse[StaffResponse]:
    created = await service.create_staff(payload, actor=actor)
    return success_response(created, message="Staff created")


@router.put(
    "/{staff_id}",
    summary="Update staff",
    description="Update staff fields. Commission percentage is ADMIN-only.",
    response_model=APIResponse[StaffResponse],
)
async def update_staff(
    staff_id: UUID,
    payload: StaffUpdateRequest,
    service: StaffServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.STAFF_WRITE)),
) -> APIResponse[StaffResponse]:
    updated = await service.update_staff(staff_id, payload, actor=actor)
    return success_response(updated, message="Staff updated")


@router.delete(
    "/{staff_id}",
    summary="Deactivate staff",
    description="Soft-delete a staff profile, set status INACTIVE, and disable login.",
    response_model=APIResponse[None],
)
async def deactivate_staff(
    staff_id: UUID,
    service: StaffServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.STAFF_DELETE)),
) -> APIResponse[None]:
    await service.deactivate_staff(staff_id, actor=actor)
    return success_response(message="Staff deactivated")
