from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.staff.repository import StaffRepository
from app.staff.service import StaffService


def get_staff_service(session: SessionDep) -> StaffService:
    return StaffService(StaffRepository(session))


StaffServiceDep = Annotated[StaffService, Depends(get_staff_service)]
