from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardOverviewResponse(BaseModel):
    as_of: datetime
    revenue_today: Decimal
    revenue_this_month: Decimal
    appointments_today: int
    customers_served: int
    average_ticket_size: Decimal


class RevenuePointResponse(BaseModel):
    period: str
    revenue: Decimal


class RevenueSeriesResponse(BaseModel):
    group_by: str
    start_date: date
    end_date: date
    items: list[RevenuePointResponse]


class AppointmentDayResponse(BaseModel):
    appointment_date: date
    total: int
    completed: int
    cancelled: int


class AppointmentSeriesResponse(BaseModel):
    start_date: date
    end_date: date
    items: list[AppointmentDayResponse]


class TopPerformerResponse(BaseModel):
    staff_id: UUID
    staff_name: str
    revenue: Decimal
    appointments_completed: int


class TopPerformersResponse(BaseModel):
    start_date: date
    end_date: date
    items: list[TopPerformerResponse] = Field(default_factory=list)
