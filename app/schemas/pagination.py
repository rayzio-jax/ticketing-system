from pydantic import BaseModel, ConfigDict, Field


class ListParamsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None


class Page[T](BaseModel):
    data: list[T]
    next_cursor: str | None = None
