from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums import AppointmentStatus
from app.customers.schemas import CustomerCreateRequest


class AppointmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID | None = None
    customer: CustomerCreateRequest | None = None
    staff_id: UUID
    appointment_date: date
    start_time: time
    service_ids: list[UUID] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def require_customer(self) -> AppointmentCreateRequest:
        if self.customer_id is None and self.customer is None:
            raise ValueError("customer_id or customer is required")
        if self.customer_id is not None and self.customer is not None:
            raise ValueError("Provide customer_id or customer, not both")
        if len(set(self.service_ids)) != len(self.service_ids):
            raise ValueError("Duplicate services are not allowed")
        if self.notes is not None:
            stripped = self.notes.strip()
            self.notes = stripped or None
        return self


class AppointmentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, max_length=5000)
    staff_id: UUID | None = None
    customer_id: UUID | None = None
    service_ids: list[UUID] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_one_field(self) -> AppointmentUpdateRequest:
        changes = self.model_dump(exclude_unset=True)
        if not changes:
            raise ValueError("At least one field is required")
        if "service_ids" in changes and len(set(self.service_ids or [])) != len(
            self.service_ids or []
        ):
            raise ValueError("Duplicate services are not allowed")
        if "notes" in changes and self.notes is not None:
            stripped = self.notes.strip()
            self.notes = stripped or None
        return self


class AppointmentStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AppointmentStatus
    staff_id: UUID | None = None


class AppointmentRescheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_date: date
    start_time: time
    staff_id: UUID | None = None


class AppointmentLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_id: UUID
    service_name: str
    duration_minutes: int
    price: Decimal


class AppointmentResponse(BaseModel):
    id: UUID
    customer_id: UUID
    customer_name: str
    customer_phone: str
    staff_id: UUID
    staff_name: str
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    notes: str | None
    duration_minutes: int
    services: list[AppointmentLineResponse]
    cancelled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CalendarDayResponse(BaseModel):
    date: date
    appointments: list[AppointmentResponse]


class CalendarResponse(BaseModel):
    start_date: date
    end_date: date
    days: list[CalendarDayResponse]
