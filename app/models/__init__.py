"""SQLAlchemy ORM models.

Importing from this package ensures every mapped class is registered on
``Base.metadata`` before ``create_all`` runs.
"""

from app.models.comment import Comment
from app.models.tag import Tag, ticket_tags
from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from app.models.user import User, UserRole

__all__ = [
    "Comment",
    "Tag",
    "Ticket",
    "TicketCategory",
    "TicketPriority",
    "TicketStatus",
    "User",
    "UserRole",
    "ticket_tags",
]
