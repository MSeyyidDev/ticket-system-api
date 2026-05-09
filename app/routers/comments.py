"""Comment endpoints attached under /tickets/{id}/comments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead
from app.services.comment_service import CommentService

router = APIRouter(prefix="/tickets/{ticket_id}/comments", tags=["comments"])


@router.get(
    "",
    response_model=list[CommentRead],
    summary="List all comments on a ticket",
)
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CommentRead]:
    items = CommentService(db).list(ticket_id)
    return [CommentRead.model_validate(c) for c in items]


@router.post(
    "",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Post a new comment on a ticket",
)
def add_comment(
    ticket_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    comment = CommentService(db).add(ticket_id, payload, author=current_user)
    return CommentRead.model_validate(comment)
