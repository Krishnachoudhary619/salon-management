from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import PaymentMethod, PaymentStatus


class PaymentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.SUCCESS


class InvoiceLineResponse(BaseModel):
    service_id: UUID
    service_name: str
    duration_minutes: int
    price: Decimal


class InvoiceResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    invoice_number: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    paid_amount: Decimal
    is_paid: bool
    line_items: list[InvoiceLineResponse]
    created_at: datetime
    updated_at: datetime


class PaymentResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    invoice_id: UUID | None = None
    amount: Decimal
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
