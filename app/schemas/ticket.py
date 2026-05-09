"""Ticket payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ticket import TicketCategory, TicketPriority, TicketStatus
from app.schemas.tag import TagRead
from app.schemas.user import UserRead


class TicketBase(BaseModel):
    """Fields shared by create and update payloads."""

    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=1, max_length=10_000)
    priority: TicketPriority = TicketPriority.MEDIUM
    category: TicketCategory = TicketCategory.OTHER


class TicketCreate(TicketBase):
    """Payload to open a new ticket."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Laptop will not boot after Windows update",
                    "description": "Since this morning the laptop hangs on the spinning dots.\n\nI tried a hard reboot but the issue persists.",
                    "priority": "high",
                    "category": "Hardware",
                    "tags": ["windows", "boot"],
                }
            ]
        }
    )

    assignee_id: int | None = Field(
        default=None,
        description="Optional agent to immediately assign the ticket to.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tag names — created on the fly if they do not exist yet.",
    )


class TicketUpdate(BaseModel):
    """Patch-style update for an existing ticket."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    priority: TicketPriority | None = None
    category: TicketCategory | None = None
    tags: list[str] | None = None


class TicketStatusUpdate(BaseModel):
    """Move a ticket along its lifecycle."""

    status: TicketStatus


class TicketAssign(BaseModel):
    """Reassign a ticket to a different agent (or unassign with ``null``)."""

    assignee_id: int | None = Field(default=None, description="Target agent user id.")


class TicketRead(TicketBase):
    """Public representation of a ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TicketStatus
    requester: UserRead
    assignee: UserRead | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    sla_due_at: datetime | None = None
    tags: list[TagRead] = Field(default_factory=list)
    comment_count: int = Field(default=0, ge=0)
