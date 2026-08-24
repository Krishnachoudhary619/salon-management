from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CommissionResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    staff_id: UUID
    staff_name: str
    service_revenue: Decimal
    commission_percentage: Decimal
    commission_amount: Decimal
    created_at: datetime
    updated_at: datetime
