"""Database access for ticket comments."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.comment import Comment


class CommentRepository:
    """Single point of access for the ``comments`` table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_ticket(self, ticket_id: int) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.ticket_id == ticket_id)
            .order_by(Comment.created_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    def add(self, comment: Comment) -> Comment:
        self.db.add(comment)
        self.db.flush()
        return comment

    def count(self) -> int:
        return int(self.db.execute(select(func.count(Comment.id))).scalar_one())
