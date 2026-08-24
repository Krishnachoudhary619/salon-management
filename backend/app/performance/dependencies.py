from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.performance.repository import PerformanceRepository
from app.performance.service import PerformanceService
from app.staff.repository import StaffRepository


def get_performance_service(session: SessionDep) -> PerformanceService:
    return PerformanceService(
        PerformanceRepository(session),
        staff_repository=StaffRepository(session),
    )


PerformanceServiceDep = Annotated[PerformanceService, Depends(get_performance_service)]
