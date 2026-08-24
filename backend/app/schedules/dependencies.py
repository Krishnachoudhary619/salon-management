from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.schedules.repository import ScheduleRepository
from app.schedules.service import ScheduleService


def get_schedule_service(session: SessionDep) -> ScheduleService:
    return ScheduleService(ScheduleRepository(session))


ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]
