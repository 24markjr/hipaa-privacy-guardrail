"""Admin API for the dashboard.

Reads the immutable audit log (off the request path of the gateway's hot
endpoints) and returns aggregates + recent records. Auth-protected — these
expose operational data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.audit.reader import aggregate, read_records
from app.config import Settings
from app.dependencies import settings_dep

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/stats")
async def stats(
    limit: int = Query(1000, ge=1, le=100_000),
    settings: Settings = Depends(settings_dep),
) -> dict:
    records = read_records(settings.audit_log_path, limit=limit)
    return aggregate(records)


@router.get("/audit")
async def audit(
    limit: int = Query(50, ge=1, le=1000),
    settings: Settings = Depends(settings_dep),
) -> dict:
    records = read_records(settings.audit_log_path, limit=limit)
    return {"count": len(records), "records": list(reversed(records))}
