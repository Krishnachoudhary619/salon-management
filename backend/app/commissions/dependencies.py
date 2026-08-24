from typing import Annotated

from fastapi import Depends

from app.billing.repository import (
    BillingAppointmentRepository,
    InvoiceRepository,
    PaymentRepository,
)
from app.commissions.repository import CommissionRepository
from app.commissions.service import CommissionService
from app.common.dependencies import SessionDep
from app.staff.repository import StaffRepository


def get_commission_service(session: SessionDep) -> CommissionService:
    return CommissionService(
        CommissionRepository(session),
        appointments=BillingAppointmentRepository(session),
        invoice_repository=InvoiceRepository(session),
        payment_repository=PaymentRepository(session),
        staff_repository=StaffRepository(session),
    )


CommissionServiceDep = Annotated[CommissionService, Depends(get_commission_service)]
