"""Tag listing endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.tag import TagRead
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "",
    response_model=list[TagRead],
    summary="List every tag known to the system",
)
def list_tags(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TagRead]:
    return [TagRead.model_validate(t) for t in TagService(db).list()]
