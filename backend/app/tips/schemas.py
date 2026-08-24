from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _strip_notes(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class TipCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        return _strip_notes(value)


class TipUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        return _strip_notes(value)

    @model_validator(mode="after")
    def require_one_field(self) -> TipUpdateRequest:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("At least one field is required")
        return self


class TipResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    staff_id: UUID
    staff_name: str
    amount: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime
