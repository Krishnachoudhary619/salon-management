from typing import Annotated

from fastapi import Depends

from app.common.dependencies import SessionDep
from app.dashboard.repository import DashboardRepository
from app.dashboard.service import DashboardService


def get_dashboard_service(session: SessionDep) -> DashboardService:
    return DashboardService(DashboardRepository(session))


DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]
