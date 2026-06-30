"""Database bootstrap.

If ``NEON_DATABASE_URL`` is set, open an asyncpg pool, apply the schema, and use
the Postgres repositories. Otherwise fall back to in-memory repositories so the
gateway runs locally and in tests without a database.
"""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.config import Settings
from app.db.history import HistoryRepository, InMemoryHistoryRepository, PgHistoryRepository
from app.db.users import InMemoryUserRepository, PgUserRepository, UserRepository

_log = logging.getLogger("gateway.db")
_SCHEMA = Path(__file__).resolve().parent / "schema.sql"

# Query params present in some managed-Postgres URLs (e.g. Neon) that asyncpg
# does not accept and would raise on.
_UNSUPPORTED_DSN_PARAMS = {"channel_binding"}


def _clean_dsn(dsn: str) -> str:
    """Strip DSN query params asyncpg can't parse (keeps sslmode etc.)."""
    parts = urlsplit(dsn)
    kept = [(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_DSN_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(kept)))


async def build_repositories(
    settings: Settings,
) -> tuple[UserRepository, HistoryRepository, object | None]:
    """Return (users_repo, history_repo, pool_or_None)."""
    if not settings.neon_database_url:
        _log.warning("NEON_DATABASE_URL not set — using in-memory repositories (not durable)")
        return InMemoryUserRepository(), InMemoryHistoryRepository(), None

    import asyncpg  # local import so the dep is optional at import time

    pool = await asyncpg.create_pool(
        dsn=_clean_dsn(settings.neon_database_url), min_size=1, max_size=10
    )
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA.read_text(encoding="utf-8"))
    _log.info("connected to Postgres and applied schema")
    return PgUserRepository(pool), PgHistoryRepository(pool), pool
