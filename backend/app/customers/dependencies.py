from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.customers.repository import CustomerRepository
from app.customers.service import CustomerService


def get_customer_service(session: SessionDep) -> CustomerService:
    return CustomerService(CustomerRepository(session))


CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
