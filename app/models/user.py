"""User ORM model."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.ticket import Ticket


class UserRole(str, enum.Enum):
    """Authorisation role of a user."""

    REQUESTER = "requester"
    AGENT = "agent"
    ADMIN = "admin"


class User(Base):
    """A person interacting with the ticket system."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.REQUESTER, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    requested_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="requester",
        foreign_keys="Ticket.requester_id",
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="assignee",
        foreign_keys="Ticket.assignee_id",
    )
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="author")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User id={self.id} email={self.email!r} role={self.role.value}>"
