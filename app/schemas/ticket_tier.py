from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import PatchSchema


class TierCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    price: int = Field(ge=0)
    quota: int = Field(gt=0)


class TierUpdate(PatchSchema):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str | None = None
    price: int | None = Field(default=None, ge=0)
    quota: int | None = Field(default=None, gt=0)


class TierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    name: str
    price: int
    quota: int
    created_at: datetime


class EventInfo(BaseModel):
    id: UUID
    name: str


class TierDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    price: int
    quota: int
    event: EventInfo
    created_at: datetime
