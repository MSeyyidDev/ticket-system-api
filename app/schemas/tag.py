"""Tag payloads."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TagRead(BaseModel):
    """Public representation of a tag."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(..., min_length=1, max_length=50)
