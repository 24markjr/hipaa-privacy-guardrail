"""Non-blocking history sink.

Same principle as the audit logger: the request path only does ``queue.put_nowait``
(O(1), no DB I/O); a background worker drains records into the history repository
(Neon). This keeps Postgres entirely off the gateway's hot path — the review's
core constraint.
"""

from __future__ import annotations

import asyncio
import logging

from app.db.history import HistoryRepository
from app.db.models import AnalysisRecord

_log = logging.getLogger("gateway.history")


class HistorySink:
    def __init__(self, repo: HistoryRepository, maxsize: int = 10_000) -> None:
        self._repo = repo
        self._queue: asyncio.Queue[AnalysisRecord] = asyncio.Queue(maxsize=maxsize)
        self._task: asyncio.Task | None = None
        self._dropped = 0

    @property
    def dropped(self) -> int:
        return self._dropped

    def log(self, record: AnalysisRecord) -> None:
        """Enqueue without blocking; drop (and count) if the queue is full."""
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            self._dropped += 1

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="history-sink")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        while not self._queue.empty():
            try:
                await self._repo.add(self._queue.get_nowait())
            except Exception:  # noqa: BLE001
                _log.exception("failed to flush history record on shutdown")

    async def _run(self) -> None:
        while True:
            record = await self._queue.get()
            try:
                await self._repo.add(record)
            except Exception:  # noqa: BLE001 — never let the worker die
                _log.exception("failed to write history record")
            finally:
                self._queue.task_done()
