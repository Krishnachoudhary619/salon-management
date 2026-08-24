from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class StaffMetricsResponse(BaseModel):
    staff_id: UUID
    staff_name: str
    revenue_generated: Decimal
    customers_served: int
    appointments_completed: int
    tips_earned: Decimal
    commission_earned: Decimal


class TeamPerformanceResponse(BaseModel):
    start_date: date
    end_date: date
    items: list[StaffMetricsResponse] = Field(default_factory=list)


class StaffPerformanceResponse(StaffMetricsResponse):
    start_date: date
    end_date: date
