from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus


class BookingRequest(BaseModel):
    tier_id: int
    qty: int = Field(gt=0)


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    ticket_id: int
    qty: int
    total_amount: int
    status: BookingStatus
    expires_at: datetime
    created_at: datetime
