"""Category listing endpoint — exposes the static enum values."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.ticket import TicketCategory

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[str],
    summary="List the supported ticket categories",
)
def list_categories() -> list[str]:
    return [c.value for c in TicketCategory]
