from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.models.event import EventStatus
from app.schemas.base import PatchSchema


class EventCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=3, max_length=50)
    venue: str = Field(min_length=3, max_length=50)
    start_at: AwareDatetime


class EventUpdate(PatchSchema):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=3, max_length=50)
    venue: str | None = Field(default=None, min_length=3, max_length=50)
    status: EventStatus | None = None
    start_at: AwareDatetime | None = None


class TierInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: int
    quota: int
    sold: int = Field(exclude=True)
    created_at: datetime


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    venue: str
    status: EventStatus
    start_at: datetime
    created_at: datetime


class EventDetailResponse(EventResponse):
    tiers: list[TierInfo]


class EventListParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None
    order: Literal["asc", "desc"] = "asc"


class EventListResponse(BaseModel):
    items: list[EventResponse]
    next_cursor: str | None
