from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.models.event import EventStatus


class EventCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=3, max_length=50)
    venue: str = Field(min_length=3, max_length=50)
    start_at: AwareDatetime


class EventUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=3, max_length=50)
    venue: str | None = Field(default=None, min_length=3, max_length=50)
    status: EventStatus | None = None
    start_at: AwareDatetime | None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    venue: str
    status: EventStatus
    start_at: datetime
    created_at: datetime
