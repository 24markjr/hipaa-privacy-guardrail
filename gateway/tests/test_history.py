"""P2 — history sink (off hot path) + GET /v1/history."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from app.db.history import InMemoryHistoryRepository
from app.db.models import AnalysisRecord
from app.dependencies import history_repo_dep
from app.history.sink import HistorySink
from app.main import create_app


async def test_sink_writes_to_repo():
    repo = InMemoryHistoryRepository()
    sink = HistorySink(repo)
    await sink.start()
    sink.log(AnalysisRecord(user_id="u1", request_id="r1", endpoint="/v1/analyze", provider="echo"))
    await asyncio.wait_for(sink._queue.join(), timeout=5)
    await sink.stop()
    rows = await repo.list_for_user("u1")
    assert len(rows) == 1
    assert rows[0]["request_id"] == "r1"


async def test_sink_log_never_blocks_and_drops_when_full():
    repo = InMemoryHistoryRepository()
    sink = HistorySink(repo, maxsize=2)  # no worker started
    for i in range(5):
        sink.log(AnalysisRecord(user_id="u", request_id=str(i), endpoint="/v1/analyze", provider="e"))
    assert sink.dropped == 3


def test_history_record_is_phi_free():
    rec = AnalysisRecord(
        user_id="u1", request_id="r1", endpoint="/v1/analyze", provider="gemini",
        masked_summary="Patient <PERSON_1> presents with cough.",
    )
    d = rec.to_dict()
    # Only de-identified fields exist; no raw note / finalSummary / mapping keys.
    assert "masked_summary" in d
    assert "<PERSON_1>" in d["masked_summary"]
    assert "original" not in d and "finalSummary" not in d


@pytest.fixture
def app_with_history():
    repo = InMemoryHistoryRepository()
    app = create_app()
    app.dependency_overrides[history_repo_dep] = lambda: repo
    return app, repo


async def test_history_endpoint_requires_auth(app_with_history):
    app, _ = app_with_history
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/v1/history")
    assert r.status_code == 401
