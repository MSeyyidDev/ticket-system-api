"""Tag ORM model and the ticket-tag association table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ticket import Ticket


# Many-to-many association table between tickets and tags.
ticket_tags = Table(
    "ticket_tags",
    Base.metadata,
    Column("ticket_id", ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """A free-form label that can be attached to many tickets."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        secondary=ticket_tags,
        back_populates="tags",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tag id={self.id} name={self.name!r}>"
