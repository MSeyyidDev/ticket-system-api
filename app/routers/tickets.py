"""Ticket endpoints — the heart of the API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_agent_or_admin
from app.models.ticket import TicketCategory, TicketPriority, TicketStatus
from app.models.user import User
from app.repositories.ticket_repository import TicketFilters
from app.schemas.common import Page
from app.schemas.ticket import (
    TicketAssign,
    TicketCreate,
    TicketRead,
    TicketStatusUpdate,
    TicketUpdate,
)
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get(
    "",
    response_model=Page[TicketRead],
    summary="List tickets with filters, sorting and pagination",
)
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = Query(default=None),
    category: TicketCategory | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    requester_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    sort: str = Query(
        default="-created_at",
        description="Sort key. Prefix with '-' to invert. Allowed: created_at, updated_at, priority, status.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page[TicketRead]:
    filters = TicketFilters(
        status=status_filter,
        priority=priority,
        category=category,
        assignee_id=assignee_id,
        requester_id=requester_id,
        search=search,
        sort=sort,
    )
    return TicketService(db).list(filters, page=page, page_size=page_size)


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
    summary="Open a new ticket",
)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    service = TicketService(db)
    ticket = service.create(payload, requester=current_user)
    return service.to_read(ticket)


@router.get(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Fetch a single ticket",
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TicketRead:
    service = TicketService(db)
    return service.to_read(service.get(ticket_id))


@router.put(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Update an existing ticket (agent / admin)",
)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_agent_or_admin),
) -> TicketRead:
    service = TicketService(db)
    return service.to_read(service.update(ticket_id, payload))


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a ticket (agent / admin)",
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_agent_or_admin),
) -> Response:
    TicketService(db).delete(ticket_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{ticket_id}/assign",
    response_model=TicketRead,
    summary="Assign or unassign a ticket (agent / admin)",
)
def assign_ticket(
    ticket_id: int,
    payload: TicketAssign,
    db: Session = Depends(get_db),
    _: User = Depends(require_agent_or_admin),
) -> TicketRead:
    service = TicketService(db)
    return service.to_read(service.assign(ticket_id, payload.assignee_id))


@router.post(
    "/{ticket_id}/status",
    response_model=TicketRead,
    summary="Move a ticket through its lifecycle (state machine validated)",
)
def change_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_agent_or_admin),
) -> TicketRead:
    service = TicketService(db)
    return service.to_read(service.change_status(ticket_id, payload.status))
