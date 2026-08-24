from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.common.dependencies import PaginationDep
from app.common.enums import Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.services.dependencies import ServiceServiceDep
from app.services.schemas import ServiceCreateRequest, ServiceResponse, ServiceUpdateRequest

router = APIRouter(prefix="/services", tags=["Services"])


@router.get(
    "",
    summary="List services",
    description="Paginated service catalog. Search name, description, and category.",
    response_model=APIResponse[PaginatedData[ServiceResponse]],
)
async def list_services(
    pagination: PaginationDep,
    catalog: ServiceServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.SERVICE_READ)),
    is_active: bool | None = Query(default=None),
    category: str | None = Query(default=None),
) -> APIResponse[PaginatedData[ServiceResponse]]:
    page = await catalog.list_services(pagination, is_active=is_active, category=category)
    return success_response(page)


@router.post(
    "",
    summary="Create service",
    description="Add a catalog service.",
    response_model=APIResponse[ServiceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    payload: ServiceCreateRequest,
    catalog: ServiceServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SERVICE_WRITE)),
) -> APIResponse[ServiceResponse]:
    created = await catalog.create_service(payload, actor=actor)
    return success_response(created, message="Service created")


@router.put(
    "/{service_id}",
    summary="Update service",
    description="Update catalog fields. Price and duration changes do not rewrite past bookings.",
    response_model=APIResponse[ServiceResponse],
)
async def update_service(
    service_id: UUID,
    payload: ServiceUpdateRequest,
    catalog: ServiceServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SERVICE_WRITE)),
) -> APIResponse[ServiceResponse]:
    updated = await catalog.update_service(service_id, payload, actor=actor)
    return success_response(updated, message="Service updated")


@router.delete(
    "/{service_id}",
    summary="Deactivate service",
    description="Hide a service from new bookings by setting is_active to false.",
    response_model=APIResponse[None],
)
async def deactivate_service(
    service_id: UUID,
    catalog: ServiceServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.SERVICE_DELETE)),
) -> APIResponse[None]:
    await catalog.deactivate_service(service_id, actor=actor)
    return success_response(message="Service deactivated")
