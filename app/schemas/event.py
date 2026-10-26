from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints

from app.models.event import EventStatus

StrConst = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)
]


class EventCreate(BaseModel):
    name: StrConst
    venue: StrConst
    start_at: AwareDatetime


class EventUpdate(BaseModel):
    name: StrConst | None = None
    venue: StrConst | None = None
    status: EventStatus | None = None
    start_at: AwareDatetime | None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: StrConst
    venue: StrConst
    status: EventStatus
    start_at: datetime
    created_at: datetime
