from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.billing.dependencies import BillingServiceDep
from app.billing.schemas import InvoiceResponse, PaymentCreateRequest, PaymentResponse
from app.common.dependencies import PaginationDep
from app.common.enums import PaymentMethod, PaymentStatus, Permission
from app.common.pagination import PaginatedData
from app.common.responses import APIResponse, success_response
from app.core.permissions import require_permissions
from app.core.security import CurrentUser

payments_router = APIRouter(prefix="/payments", tags=["Billing"])
invoices_router = APIRouter(prefix="/invoices", tags=["Billing"])


@payments_router.get(
    "",
    summary="Payment history",
    description="Paginated payment audit trail. Filter by appointment, method, or status.",
    response_model=APIResponse[PaginatedData[PaymentResponse]],
)
async def list_payments(
    pagination: PaginationDep,
    billing: BillingServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.PAYMENT_READ)),
    appointment_id: UUID | None = Query(default=None),
    payment_method: PaymentMethod | None = Query(default=None),
    payment_status: PaymentStatus | None = Query(default=None, alias="status"),
) -> APIResponse[PaginatedData[PaymentResponse]]:
    page = await billing.list_payments(
        pagination,
        appointment_id=appointment_id,
        payment_method=payment_method,
        payment_status=payment_status,
    )
    return success_response(page)


@payments_router.post(
    "",
    summary="Create payment",
    description="Record a CASH, CARD, or UPI payment against a completed appointment invoice.",
    response_model=APIResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payload: PaymentCreateRequest,
    billing: BillingServiceDep,
    actor: CurrentUser = Depends(require_permissions(Permission.PAYMENT_WRITE)),
) -> APIResponse[PaymentResponse]:
    created = await billing.create_payment(payload, actor=actor)
    return success_response(created, message="Payment recorded")


@invoices_router.get(
    "",
    summary="List invoices",
    description="Paginated invoices. Filter by appointment after completion.",
    response_model=APIResponse[PaginatedData[InvoiceResponse]],
)
async def list_invoices(
    pagination: PaginationDep,
    billing: BillingServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.INVOICE_READ)),
    appointment_id: UUID | None = Query(default=None),
) -> APIResponse[PaginatedData[InvoiceResponse]]:
    page = await billing.list_invoices(pagination, appointment_id=appointment_id)
    return success_response(page)


@invoices_router.get(
    "/{invoice_id}",
    summary="Get invoice",
    description="Retrieve an invoice with line items and paid balance.",
    response_model=APIResponse[InvoiceResponse],
)
async def get_invoice(
    invoice_id: UUID,
    billing: BillingServiceDep,
    _user: CurrentUser = Depends(require_permissions(Permission.INVOICE_READ)),
) -> APIResponse[InvoiceResponse]:
    return success_response(await billing.get_invoice(invoice_id))
