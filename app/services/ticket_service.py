"""Ticket business logic, including the status state machine."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.repositories.tag_repository import TagRepository
from app.repositories.ticket_repository import TicketFilters, TicketRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate

# Allowed transitions for the ticket lifecycle.
_ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.CLOSED},
    TicketStatus.IN_PROGRESS: {
        TicketStatus.PENDING,
        TicketStatus.RESOLVED,
        TicketStatus.OPEN,
    },
    TicketStatus.PENDING: {TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.OPEN},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.IN_PROGRESS},
    TicketStatus.CLOSED: set(),
}

INVALID_TRANSITION = "Invalid status transition for this ticket."


def is_valid_transition(current: TicketStatus, target: TicketStatus) -> bool:
    """Return True iff ``current`` may legally move to ``target``."""
    if current == target:
        return False
    return target in _ALLOWED_TRANSITIONS.get(current, set())


class TicketService:
    """Owns the ticket lifecycle, including status, assignment, and tagging."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tickets = TicketRepository(db)
        self.users = UserRepository(db)
        self.tags = TagRepository(db)

    # --- read operations --------------------------------------------------------

    def list(
        self, filters: TicketFilters, *, page: int, page_size: int
    ) -> Page[TicketRead]:
        items, total = self.tickets.list(filters, page=page, page_size=page_size)
        counts = self.tickets.comment_counts([t.id for t in items])
        reads: list[TicketRead] = []
        for ticket in items:
            read = TicketRead.model_validate(ticket)
            read.comment_count = counts.get(ticket.id, 0)
            reads.append(read)
        return Page[TicketRead](items=reads, total=total, page=page, page_size=page_size)

    def get(self, ticket_id: int) -> Ticket:
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found."
            )
        return ticket

    def to_read(self, ticket: Ticket) -> TicketRead:
        read = TicketRead.model_validate(ticket)
        read.comment_count = len(ticket.comments)
        return read

    # --- mutations --------------------------------------------------------------

    def create(self, payload: TicketCreate, requester: User) -> Ticket:
        assignee: User | None = None
        if payload.assignee_id is not None:
            assignee = self.users.get(payload.assignee_id)
            if assignee is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee user does not exist.",
                )
            if assignee.role == UserRole.REQUESTER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A requester cannot be assigned to a ticket.",
                )

        ticket = Ticket(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            category=payload.category,
            requester_id=requester.id,
            assignee_id=assignee.id if assignee else None,
            status=TicketStatus.OPEN,
        )
        if payload.tags:
            ticket.tags = self.tags.get_or_create_many(payload.tags)
        self.tickets.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def update(self, ticket_id: int, payload: TicketUpdate) -> Ticket:
        ticket = self.get(ticket_id)
        data = payload.model_dump(exclude_unset=True)
        new_tags = data.pop("tags", None)
        for field, value in data.items():
            setattr(ticket, field, value)
        if new_tags is not None:
            ticket.tags = self.tags.get_or_create_many(new_tags)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def delete(self, ticket_id: int) -> None:
        ticket = self.get(ticket_id)
        self.tickets.delete(ticket)
        self.db.commit()

    def assign(self, ticket_id: int, assignee_id: int | None) -> Ticket:
        ticket = self.get(ticket_id)
        if assignee_id is None:
            ticket.assignee_id = None
        else:
            assignee = self.users.get(assignee_id)
            if assignee is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee user does not exist.",
                )
            if assignee.role == UserRole.REQUESTER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A requester cannot be assigned to a ticket.",
                )
            ticket.assignee_id = assignee.id
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def change_status(self, ticket_id: int, target: TicketStatus) -> Ticket:
        ticket = self.get(ticket_id)
        if not is_valid_transition(ticket.status, target):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"{INVALID_TRANSITION} "
                    f"Current status '{ticket.status.value}' cannot move to '{target.value}'."
                ),
            )
        ticket.status = target
        if target in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
            if ticket.resolved_at is None:
                ticket.resolved_at = datetime.now(timezone.utc)
        else:
            ticket.resolved_at = None
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
