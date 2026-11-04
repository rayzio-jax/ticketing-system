from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

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

    id: int
    event_id: UUID
    name: str
    price: int
    quota: int
    sold: int = Field(exclude=True)

    @computed_field
    @property
    def available(self) -> int:
        return self.quota - self.sold

    created_at: datetime
