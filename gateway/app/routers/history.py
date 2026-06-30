"""GET /v1/history — the logged-in doctor's past analyses (PHI-free)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.dependencies import current_user_id, history_repo_dep

if TYPE_CHECKING:
    from app.db.history import HistoryRepository

router = APIRouter(prefix="/v1", tags=["history"])


@router.get("/history")
async def history(
    limit: int = Query(50, ge=1, le=500),
    user_id: str = Depends(current_user_id),
    repo: "HistoryRepository" = Depends(history_repo_dep),
) -> dict:
    records = await repo.list_for_user(user_id, limit=limit)
    return {"count": len(records), "records": records}
