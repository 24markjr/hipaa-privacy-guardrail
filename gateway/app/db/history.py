"""Analysis-history repository — Postgres (asyncpg) and in-memory."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Protocol

from app.db.models import AnalysisRecord


class HistoryRepository(Protocol):
    async def add(self, record: AnalysisRecord) -> None: ...
    async def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]: ...


class InMemoryHistoryRepository:
    def __init__(self) -> None:
        self._rows: list[AnalysisRecord] = []

    async def add(self, record: AnalysisRecord) -> None:
        if record.created_at is None:
            record.created_at = datetime.now(timezone.utc)
        self._rows.append(record)

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        rows = [r for r in self._rows if r.user_id == user_id]
        rows.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
        return [r.to_dict() for r in rows[:limit]]


class PgHistoryRepository:
    def __init__(self, pool) -> None:
        self._pool = pool

    async def add(self, record: AnalysisRecord) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO analyses
                  (user_id, request_id, endpoint, provider, pii_count, entity_types,
                   injection_flag, blocked, processing_ms, masked_summary)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                """,
                uuid.UUID(record.user_id),
                record.request_id,
                record.endpoint,
                record.provider,
                record.pii_count,
                record.entity_types,
                record.injection_flag,
                record.blocked,
                record.processing_ms,
                record.masked_summary,
            )

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT request_id, endpoint, provider, pii_count, entity_types,
                       injection_flag, blocked, processing_ms, masked_summary, created_at
                FROM analyses WHERE user_id = $1
                ORDER BY created_at DESC LIMIT $2
                """,
                uuid.UUID(user_id),
                limit,
            )
        return [
            {
                "request_id": r["request_id"],
                "endpoint": r["endpoint"],
                "provider": r["provider"],
                "pii_count": r["pii_count"],
                "entity_types": list(r["entity_types"]),
                "injection_flag": r["injection_flag"],
                "blocked": r["blocked"],
                "processing_ms": r["processing_ms"],
                "masked_summary": r["masked_summary"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
