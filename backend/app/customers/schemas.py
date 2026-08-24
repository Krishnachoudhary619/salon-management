from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

_PHONE_PATTERN = re.compile(r"^[0-9]{10,15}$")


def _validate_phone(value: str) -> str:
    if not _PHONE_PATTERN.fullmatch(value):
        raise ValueError("Phone must be 10-15 digits")
    return value


def _normalize_text(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Value cannot be empty")
    return stripped


class CustomerCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=10, max_length=15)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return _normalize_text(value)

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str) -> str:
        return _validate_phone(value)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class CustomerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=10, max_length=15)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _normalize_text(value)

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_phone(value)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def require_one_field(self) -> CustomerUpdateRequest:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required")
        return self


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    email: str | None
    notes: str | None
    visit_count: int
    total_spent: Decimal
    last_visit: datetime | None
    created_at: datetime
    updated_at: datetime
