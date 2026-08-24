from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.common.enums import StaffStatus

_PHONE_PATTERN = re.compile(r"^[0-9]{10,15}$")


def _validate_phone(value: str) -> str:
    if not _PHONE_PATTERN.fullmatch(value):
        raise ValueError("Phone must be 10-15 digits")
    return value


class StaffCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)
    phone: str = Field(min_length=10, max_length=15)
    designation: str = Field(min_length=1, max_length=80)
    commission_percentage: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    joining_date: date
    status: StaffStatus = StaffStatus.ACTIVE

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str) -> str:
        return _validate_phone(value)


class StaffUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=10, max_length=15)
    designation: str | None = Field(default=None, min_length=1, max_length=80)
    commission_percentage: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    joining_date: date | None = None
    status: StaffStatus | None = None

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_phone(value)

    @model_validator(mode="after")
    def require_one_field(self) -> StaffUpdateRequest:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required")
        return self


class StaffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    email: str | None = None
    phone: str
    designation: str
    commission_percentage: Decimal
    joining_date: date
    status: StaffStatus
    created_at: datetime
    updated_at: datetime
