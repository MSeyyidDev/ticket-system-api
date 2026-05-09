"""Ticket ORM model with status, priority, and category enums."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.tag import ticket_tags

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.tag import Tag
    from app.models.user import User


class TicketStatus(str, enum.Enum):
    """Lifecycle state of a ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Severity / urgency of a ticket."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, enum.Enum):
    """Functional area the ticket belongs to."""

    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    ACCOUNT = "Account"
    EMAIL = "Email"
    SECURITY = "Security"
    OTHER = "Other"


class Ticket(Base):
    """A single support request raised by a user."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM, index=True
    )
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory), nullable=False, default=TicketCategory.OTHER, index=True
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester: Mapped["User"] = relationship(
        "User",
        back_populates="requested_tickets",
        foreign_keys=[requester_id],
        lazy="joined",
    )
    assignee: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_tickets",
        foreign_keys=[assignee_id],
        lazy="joined",
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=ticket_tags,
        back_populates="tickets",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Ticket id={self.id} status={self.status.value} title={self.title!r}>"
