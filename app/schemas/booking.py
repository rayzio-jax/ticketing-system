from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus
from app.schemas.pagination import ListParamsSchema


class BookingRequest(BaseModel):
    tier_id: int
    qty: int = Field(gt=0)


class BookingListParams(ListParamsSchema):
    order: Literal["asc", "desc"] = "desc"
    status: BookingStatus | None = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    tier_id: int
    qty: int
    total_amount: int
    status: BookingStatus
    expires_at: datetime
    created_at: datetime
