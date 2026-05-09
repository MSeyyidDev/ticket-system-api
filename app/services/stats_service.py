"""Aggregate statistics across the data set."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ticket import TicketStatus
from app.repositories.comment_repository import CommentRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository
from app.schemas.stats import StatsOverview


class StatsService:
    """Builds the dashboard payload returned by ``/stats/overview``."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tickets = TicketRepository(db)
        self.users = UserRepository(db)
        self.comments = CommentRepository(db)

    def overview(self) -> StatsOverview:
        by_status = self.tickets.count_by_status()
        avg_seconds = self.tickets.average_resolution_seconds()
        avg_hours = round(avg_seconds / 3600, 2) if avg_seconds is not None else None
        return StatsOverview(
            total_tickets=self.tickets.count(),
            open_tickets=by_status.get(TicketStatus.OPEN.value, 0),
            resolved_tickets=by_status.get(TicketStatus.RESOLVED.value, 0),
            closed_tickets=by_status.get(TicketStatus.CLOSED.value, 0),
            by_status=by_status,
            by_priority=self.tickets.count_by_priority(),
            by_category=self.tickets.count_by_category(),
            average_resolution_hours=avg_hours,
            total_users=self.users.count(),
            total_comments=self.comments.count(),
        )
