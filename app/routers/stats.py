"""Statistics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.stats import StatsOverview
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/overview",
    response_model=StatsOverview,
    summary="Aggregate KPIs across the whole ticket data set",
)
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StatsOverview:
    return StatsService(db).overview()
