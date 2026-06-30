"""Phase 9 & 11 — admin aggregation, admin endpoints, /metrics, dashboard."""

from __future__ import annotations

import json

import httpx
import pytest

from app.audit.reader import aggregate
from app.config import Settings
from app.dependencies import settings_dep
from app.main import create_app

_SAMPLE = [
    {
        "pii_count": 2, "injection_flag": False, "blocked": False, "token_count": 10,
        "estimated_cost": 0.001, "processing_time_ms": 5.0,
        "entity_types_count": {"EMAIL_ADDRESS": 2}, "policy_violations": [],
        "provider": "gemini", "endpoint": "/v1/analyze", "timestamp": "2026-01-01T00:00:00Z",
    },
    {
        "pii_count": 1, "injection_flag": True, "blocked": True, "token_count": 0,
        "estimated_cost": 0.0, "processing_time_ms": 15.0,
        "entity_types_count": {"IN_PAN": 1},
        "policy_violations": ["policy:IN_PAN", "injection:jailbreak_dan"],
        "provider": "openai", "endpoint": "/v1/chat/completions", "timestamp": "2026-01-01T00:01:00Z",
    },
]


def test_aggregate_pure():
    agg = aggregate(_SAMPLE)
    assert agg["total_requests"] == 2
    assert agg["pii_found"] == 3
    assert agg["injection_attempts"] == 1
    assert agg["blocked"] == 1
    assert agg["token_usage"] == 10
    assert agg["entity_types"] == {"EMAIL_ADDRESS": 2, "IN_PAN": 1}
    assert agg["provider_usage"] == {"gemini": 1, "openai": 1}
    assert agg["policy_violations"] == {"IN_PAN": 1, "jailbreak_dan": 1}
    assert agg["latency_ms"]["p99"] >= agg["latency_ms"]["p50"]


def test_aggregate_empty():
    agg = aggregate([])
    assert agg["total_requests"] == 0
    assert agg["latency_ms"]["p95"] == 0.0


@pytest.fixture
def app_and_client(tmp_path):
    path = tmp_path / "audit.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in _SAMPLE), encoding="utf-8")
    app = create_app()
    app.dependency_overrides[settings_dep] = lambda: Settings(audit_log_path=str(path))
    return app


async def _client(app):
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-API-Key": "dev-local-key"}
    )


async def test_admin_stats_endpoint(app_and_client):
    async with await _client(app_and_client) as c:
        r = await c.get("/v1/admin/stats")
        assert r.status_code == 200
        assert r.json()["total_requests"] == 2
        r = await c.get("/v1/admin/audit")
        assert r.status_code == 200
        assert r.json()["count"] == 2


async def test_admin_requires_auth(app_and_client):
    transport = httpx.ASGITransport(app=app_and_client)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/v1/admin/stats")
    assert r.status_code == 401


async def test_metrics_endpoint_exposes_gateway_metrics(app_and_client):
    async with await _client(app_and_client) as c:
        r = await c.get("/metrics")
    assert r.status_code == 200
    assert "gateway_requests_total" in r.text
    assert "gateway_active_requests" in r.text


async def test_dashboard_served(app_and_client):
    async with await _client(app_and_client) as c:
        r = await c.get("/dashboard")
    assert r.status_code == 200
    assert "Admin Dashboard" in r.text
