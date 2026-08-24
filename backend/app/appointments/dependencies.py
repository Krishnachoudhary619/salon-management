from typing import Annotated

from fastapi import Depends

from app.appointments.engine import AvailabilityEngine
from app.appointments.repository import AppointmentRepository
from app.appointments.service import AppointmentService
from app.billing.dependencies import get_billing_service
from app.common.dependencies import SessionDep
from app.customers.repository import CustomerRepository
from app.customers.service import CustomerService
from app.schedules.repository import ScheduleRepository
from app.staff.repository import StaffRepository


def get_appointment_service(session: SessionDep) -> AppointmentService:
    return AppointmentService(
        AppointmentRepository(session),
        availability_engine=AvailabilityEngine(ScheduleRepository(session)),
        customer_service=CustomerService(CustomerRepository(session)),
        staff_repository=StaffRepository(session),
        billing_service=get_billing_service(session),
    )


AppointmentServiceDep = Annotated[AppointmentService, Depends(get_appointment_service)]
