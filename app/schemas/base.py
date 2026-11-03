from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class PatchSchema(BaseModel):
    """Base for PATCH bodies: unknown fields and explicit nulls are rejected."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def reject_explicit_null(self) -> Self:
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self
