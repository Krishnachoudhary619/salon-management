from typing import Annotated

from fastapi import Depends

from app.billing.repository import (
    BillingAppointmentRepository,
    InvoiceRepository,
    PaymentRepository,
)
from app.billing.service import BillingService
from app.commissions.dependencies import get_commission_service
from app.common.dependencies import SessionDep
from app.customers.repository import CustomerRepository
from app.customers.service import CustomerService


def get_billing_service(session: SessionDep) -> BillingService:
    return BillingService(
        PaymentRepository(session),
        invoice_repository=InvoiceRepository(session),
        appointments=BillingAppointmentRepository(session),
        customer_service=CustomerService(CustomerRepository(session)),
        commission_service=get_commission_service(session),
    )


BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]
