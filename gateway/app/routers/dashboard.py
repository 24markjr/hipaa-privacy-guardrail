"""Serve the static admin dashboard shell.

The page itself is public (it's just HTML/JS); the data it fetches from
``/v1/admin/*`` is auth-protected, and the page prompts for the API key.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])

_DASHBOARD_HTML = Path(__file__).resolve().parents[1] / "static" / "dashboard.html"


@router.get("/dashboard", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD_HTML)
