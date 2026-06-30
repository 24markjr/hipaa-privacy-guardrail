"""Dependency-injection providers.

FastAPI routers declare what they need via ``Depends(...)`` and receive these.
Shared singletons (HTTP client, Redis) live on ``app.state`` — set up once in
the lifespan — and are handed out here. This keeps handlers testable: a test can
override any of these with a fake.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from app.config import Settings, get_settings

if TYPE_CHECKING:  # avoid importing heavy/optional deps at module load
    import httpx
    from redis.asyncio import Redis

    from app.audit.logger import AuditLogger
    from app.compliance.engine import ComplianceEngine
    from app.compliance.vault import RedisVault
    from app.db.history import HistoryRepository
    from app.db.users import UserRepository
    from app.history.sink import HistorySink
    from app.providers.base import BaseLLMProvider


def settings_dep() -> Settings:
    return get_settings()


def http_client_dep(request: Request) -> "httpx.AsyncClient":
    return request.app.state.http_client


def redis_dep(request: Request) -> "Redis":
    return request.app.state.redis


def vault_dep(request: Request) -> "RedisVault":
    return request.app.state.vault


def engine_dep(request: Request) -> "ComplianceEngine":
    return request.app.state.engine


def provider_dep(request: Request) -> "BaseLLMProvider":
    return request.app.state.provider


def providers_dep(request: Request) -> dict:
    """All providers keyed by name (for per-request selection)."""
    return getattr(request.app.state, "providers", {})


def policies_dep(request: Request) -> dict:
    """All loaded policy profiles keyed by name (for per-request selection)."""
    return getattr(request.app.state, "policies", {})


def audit_dep(request: Request) -> "AuditLogger":
    return request.app.state.audit


def users_dep(request: Request) -> "UserRepository":
    return request.app.state.users


def history_repo_dep(request: Request) -> "HistoryRepository":
    return request.app.state.history_repo


def history_sink_dep(request: Request) -> "HistorySink":
    return request.app.state.history_sink


def current_user_id(request: Request) -> str:
    """Require an authenticated doctor (JWT). 401 if absent."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="authentication required")
    return user_id
