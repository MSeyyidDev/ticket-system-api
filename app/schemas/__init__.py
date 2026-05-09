"""Pydantic v2 schemas — the public contract of the API."""

from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.comment import CommentCreate, CommentRead
from app.schemas.common import Page
from app.schemas.stats import StatsOverview
from app.schemas.tag import TagRead
from app.schemas.ticket import (
    TicketAssign,
    TicketCreate,
    TicketRead,
    TicketStatusUpdate,
    TicketUpdate,
)
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "CommentCreate",
    "CommentRead",
    "LoginRequest",
    "Page",
    "StatsOverview",
    "TagRead",
    "TicketAssign",
    "TicketCreate",
    "TicketRead",
    "TicketStatusUpdate",
    "TicketUpdate",
    "TokenResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
