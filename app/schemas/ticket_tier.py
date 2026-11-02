from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TierCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: UUID
    name: str
    price: int = Field(ge=0)
    quota: int = Field(gt=0)


class TierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    name: str
    price: int
    quota: int
    created_at: datetime
