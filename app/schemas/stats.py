"""Statistics payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StatsOverview(BaseModel):
    """High-level KPIs for a dashboard or analytics consumer."""

    total_tickets: int = Field(..., ge=0)
    open_tickets: int = Field(..., ge=0)
    resolved_tickets: int = Field(..., ge=0)
    closed_tickets: int = Field(..., ge=0)
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_category: dict[str, int]
    average_resolution_hours: float | None = Field(
        default=None,
        description="Mean time between creation and resolution for resolved/closed tickets.",
    )
    total_users: int = Field(..., ge=0)
    total_comments: int = Field(..., ge=0)
