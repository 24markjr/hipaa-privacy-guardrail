"""Liveness and readiness probes.

``/health`` — liveness: the process is up (no dependencies checked).
``/ready``  — readiness: dependencies (Redis) are reachable. Used by
              orchestrators to decide whether to route traffic here.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app import __version__
from app.config import Settings
from app.dependencies import redis_dep, settings_dep

if TYPE_CHECKING:
    from redis.asyncio import Redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: Settings = Depends(settings_dep)) -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "engine": settings.detection_engine.value,
        "provider": settings.llm_provider.value,
    }


@router.get("/ready")
async def ready(redis: "Redis" = Depends(redis_dep)) -> dict:
    checks: dict[str, str] = {}
    try:
        await asyncio.wait_for(redis.ping(), timeout=2.0)
        checks["redis"] = "ok"
    except (Exception, asyncio.TimeoutError) as exc:  # noqa: BLE001 — any failure => not ready
        checks["redis"] = f"error: {exc}"

    ready = all(v == "ok" for v in checks.values())
    return {"ready": ready, "checks": checks}
