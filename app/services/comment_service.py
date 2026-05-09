"""Comment business logic."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repository import CommentRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.comment import CommentCreate


class CommentService:
    """Coordinates ticket existence checks and comment persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.comments = CommentRepository(db)
        self.tickets = TicketRepository(db)

    def list(self, ticket_id: int) -> list[Comment]:
        if self.tickets.get(ticket_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
            )
        return self.comments.list_for_ticket(ticket_id)

    def add(self, ticket_id: int, payload: CommentCreate, author: User) -> Comment:
        if self.tickets.get(ticket_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
            )
        comment = Comment(
            ticket_id=ticket_id,
            author_id=author.id,
            body=payload.body,
            is_internal=payload.is_internal,
        )
        self.comments.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment
