"""Comment payloads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserRead


class CommentCreate(BaseModel):
    """Payload to post a new comment on a ticket."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "body": "I have rolled back the driver — please test again.",
                    "is_internal": False,
                }
            ]
        }
    )

    body: str = Field(..., min_length=1, max_length=10_000)
    is_internal: bool = False


class CommentRead(BaseModel):
    """Public representation of a comment."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    body: str
    is_internal: bool
    created_at: datetime
    author: UserRead
