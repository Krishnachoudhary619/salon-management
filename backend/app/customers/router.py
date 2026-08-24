from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.common.dependencies import PaginationDep
from app.common.enums import Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser
from app.customers.dependencies import CustomerServiceDep
from app.customers.schemas import CustomerCreateRequest, CustomerResponse, CustomerUpdateRequest

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get(
    "",
    summary="Search customers",
    description="Paginated CRM search by name, phone, or email. Optional exact phone match.",
    response_model=APIResponse[PaginatedData[CustomerResponse]],
)
async def list_customers(
    pagination: PaginationDep,
    crm: CustomerServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.CUSTOMER_READ)),
    phone: str | None = Query(default=None, min_length=10, max_length=15),
) -> APIResponse[PaginatedData[CustomerResponse]]:
    page = await crm.list_customers(pagination, phone=phone)
    return success_response(page)


@router.get(
    "/{customer_id}",
    summary="Customer profile",
    description="Return a customer profile including visit count, spend, and last visit.",
    response_model=APIResponse[CustomerResponse],
)
async def get_customer(
    customer_id: UUID,
    crm: CustomerServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.CUSTOMER_READ)),
) -> APIResponse[CustomerResponse]:
    return success_response(await crm.get_customer(customer_id))


@router.post(
    "",
    summary="Create customer",
    description="Create a CRM customer. Visit stats start at zero.",
    response_model=APIResponse[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    payload: CustomerCreateRequest,
    crm: CustomerServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.CUSTOMER_WRITE)),
) -> APIResponse[CustomerResponse]:
    created = await crm.create_customer(payload, actor=actor)
    return success_response(created, message="Customer created")


@router.put(
    "/{customer_id}",
    summary="Update customer",
    description="Update identity fields. Visit tracking fields are system-maintained.",
    response_model=APIResponse[CustomerResponse],
)
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdateRequest,
    crm: CustomerServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.CUSTOMER_WRITE)),
) -> APIResponse[CustomerResponse]:
    updated = await crm.update_customer(customer_id, payload, actor=actor)
    return success_response(updated, message="Customer updated")
