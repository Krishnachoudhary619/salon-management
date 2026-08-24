from typing import Annotated

from fastapi import Depends

from app.appointments.repository import AppointmentRepository
from app.common.dependencies import SessionDep
from app.staff.repository import StaffRepository
from app.tips.repository import TipRepository
from app.tips.service import TipService


def get_tip_service(session: SessionDep) -> TipService:
    return TipService(
        TipRepository(session),
        appointment_repository=AppointmentRepository(session),
        staff_repository=StaffRepository(session),
    )


TipServiceDep = Annotated[TipService, Depends(get_tip_service)]
