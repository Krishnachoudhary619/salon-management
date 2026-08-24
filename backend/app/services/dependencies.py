from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.services.repository import ServiceRepository
from app.services.service import ServiceService


def get_service_service(session: SessionDep) -> ServiceService:
    return ServiceService(ServiceRepository(session))


ServiceServiceDep = Annotated[ServiceService, Depends(get_service_service)]
