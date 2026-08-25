from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.customers.schemas import _validate_phone


class PublicServiceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    duration_minutes: int
    price: str
    category: str


class PublicStaffItem(BaseModel):
    id: UUID
    name: str
    designation: str


class PublicCatalogResponse(BaseModel):
    services: list[PublicServiceItem]
    staff: list[PublicStaffItem]


class PublicBookingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=10, max_length=15)
    staff_id: UUID
    service_id: UUID
    appointment_date: date
    start_time: time
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name is required")
        return stripped

    @field_validator("phone")
    @classmethod
    def phone_digits(cls, value: str) -> str:
        return _validate_phone("".join(character for character in value if character.isdigit()))

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
