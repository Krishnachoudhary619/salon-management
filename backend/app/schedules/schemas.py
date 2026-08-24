from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScheduleWindowBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day_of_week: int = Field(ge=0, le=6, description="0 = Monday … 6 = Sunday")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def end_after_start(self) -> ScheduleWindowBase:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class StaffScheduleCreateRequest(ScheduleWindowBase):
    staff_id: UUID


class StaffScheduleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def require_one_field(self) -> StaffScheduleUpdateRequest:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required")
        return self

    @model_validator(mode="after")
    def end_after_start_when_both_set(self) -> StaffScheduleUpdateRequest:
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")
        return self


class WeeklyWindowRequest(ScheduleWindowBase):
    pass


class WeeklyScheduleReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    windows: list[WeeklyWindowRequest]


class StaffScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    staff_id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    created_at: datetime
    updated_at: datetime


class WeeklyScheduleResponse(BaseModel):
    staff_id: UUID
    windows: list[StaffScheduleResponse]


class AvailabilitySlot(BaseModel):
    start_time: time
    end_time: time


class AvailabilityResponse(BaseModel):
    staff_id: UUID
    date: date
    duration_minutes: int
    slots: list[AvailabilitySlot]
