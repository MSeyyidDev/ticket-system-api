"""Generic response envelopes shared across endpoints."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """A paginated slice of a larger collection."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T] = Field(default_factory=list, description="Items in the current page.")
    total: int = Field(..., ge=0, description="Total number of items matching the query.")
    page: int = Field(..., ge=1, description="1-based page index.")
    page_size: int = Field(..., ge=1, le=200, description="Items per page.")
