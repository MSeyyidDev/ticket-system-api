"""Database access for tickets."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.comment import Comment
from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus


@dataclass(slots=True)
class TicketFilters:
    """Optional filters / sorting for the ticket list endpoint."""

    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: TicketCategory | None = None
    assignee_id: int | None = None
    requester_id: int | None = None
    search: str | None = None
    sort: str = "-created_at"  # one of: created_at, -created_at, priority, -priority


_PRIORITY_ORDER = case(
    {
        TicketPriority.LOW: 0,
        TicketPriority.MEDIUM: 1,
        TicketPriority.HIGH: 2,
        TicketPriority.CRITICAL: 3,
    },
    value=Ticket.priority,
)


class TicketRepository:
    """Encapsulates all ticket queries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- queries ----------------------------------------------------------------

    def get(self, ticket_id: int) -> Ticket | None:
        stmt = (
            select(Ticket)
            .options(selectinload(Ticket.tags), selectinload(Ticket.comments))
            .where(Ticket.id == ticket_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list(
        self, filters: TicketFilters, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[Ticket], int]:
        stmt = select(Ticket).options(selectinload(Ticket.tags))
        count_stmt = select(func.count(Ticket.id))

        clauses = []
        if filters.status is not None:
            clauses.append(Ticket.status == filters.status)
        if filters.priority is not None:
            clauses.append(Ticket.priority == filters.priority)
        if filters.category is not None:
            clauses.append(Ticket.category == filters.category)
        if filters.assignee_id is not None:
            clauses.append(Ticket.assignee_id == filters.assignee_id)
        if filters.requester_id is not None:
            clauses.append(Ticket.requester_id == filters.requester_id)
        if filters.search:
            like = f"%{filters.search.strip()}%"
            clauses.append(Ticket.title.ilike(like))

        for clause in clauses:
            stmt = stmt.where(clause)
            count_stmt = count_stmt.where(clause)

        stmt = self._apply_sort(stmt, filters.sort)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        total = int(self.db.execute(count_stmt).scalar_one())
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total

    @staticmethod
    def _apply_sort(stmt, sort: str):
        """Translate the API ``sort`` query string into an ORDER BY clause."""
        descending = sort.startswith("-")
        key = sort.lstrip("-")
        column_map = {
            "created_at": Ticket.created_at,
            "updated_at": Ticket.updated_at,
            "priority": _PRIORITY_ORDER,
            "status": Ticket.status,
        }
        column = column_map.get(key, Ticket.created_at)
        return stmt.order_by(column.desc() if descending else column.asc())

    def comment_counts(self, ticket_ids: list[int]) -> dict[int, int]:
        if not ticket_ids:
            return {}
        stmt = (
            select(Comment.ticket_id, func.count(Comment.id))
            .where(Comment.ticket_id.in_(ticket_ids))
            .group_by(Comment.ticket_id)
        )
        return {tid: int(count) for tid, count in self.db.execute(stmt).all()}

    def count(self) -> int:
        return int(self.db.execute(select(func.count(Ticket.id))).scalar_one())

    def count_by_status(self) -> dict[str, int]:
        stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        return {status.value: int(c) for status, c in self.db.execute(stmt).all()}

    def count_by_priority(self) -> dict[str, int]:
        stmt = select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
        return {priority.value: int(c) for priority, c in self.db.execute(stmt).all()}

    def count_by_category(self) -> dict[str, int]:
        stmt = select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)
        return {category.value: int(c) for category, c in self.db.execute(stmt).all()}

    def average_resolution_seconds(self) -> float | None:
        """Average wall-clock seconds between creation and resolution."""
        rows = self.db.execute(
            select(Ticket.created_at, Ticket.resolved_at).where(Ticket.resolved_at.is_not(None))
        ).all()
        if not rows:
            return None
        deltas = [(resolved - created).total_seconds() for created, resolved in rows]
        return sum(deltas) / len(deltas) if deltas else None

    # --- mutations --------------------------------------------------------------

    def add(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        self.db.flush()
        return ticket

    def delete(self, ticket: Ticket) -> None:
        self.db.delete(ticket)
        self.db.flush()
