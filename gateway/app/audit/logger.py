"""Non-blocking, append-only audit logger.

Design (per review): the request path must never wait on disk or network I/O.
So ``log()`` only does an O(1) ``queue.put_nowait`` and returns; a single
background worker drains the queue and appends JSON Lines to a local file. File
writes happen in a thread so they don't block the event loop, and a single
writer means no interleaving — records are immutable once written.

If the queue is full (a sustained burst), records are dropped and counted rather
than blocking request handling — availability over completeness for telemetry.

An optional Redis Stream fan-out (XADD) can be enabled out-of-band for the
dashboard without touching this hot path; kept off by default.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from app.audit.models import AuditRecord

_log = logging.getLogger("gateway.audit")


class AuditLogger:
    def __init__(self, path: str, maxsize: int = 10_000) -> None:
        self._path = Path(path)
        self._queue: asyncio.Queue[AuditRecord] = asyncio.Queue(maxsize=maxsize)
        self._task: asyncio.Task | None = None
        self._fh = None
        self._dropped = 0

    @property
    def dropped(self) -> int:
        return self._dropped

    def log(self, record: AuditRecord) -> None:
        """Enqueue a record. Never blocks; drops (and counts) if the queue is full."""
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            self._dropped += 1

    async def start(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self._path, "a", encoding="utf-8")  # noqa: SIM115 — long-lived
        self._task = asyncio.create_task(self._run(), name="audit-writer")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # Flush whatever is still queued (best effort, synchronous).
        while not self._queue.empty():
            self._write(self._queue.get_nowait())
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def _write(self, record: AuditRecord) -> None:
        assert self._fh is not None
        self._fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        self._fh.flush()

    async def _run(self) -> None:
        while True:
            record = await self._queue.get()
            try:
                await asyncio.to_thread(self._write, record)
            except Exception:  # noqa: BLE001 — never let the writer die silently
                _log.exception("failed to write audit record")
            finally:
                self._queue.task_done()
