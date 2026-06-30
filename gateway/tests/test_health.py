"""Phase 0/1 smoke tests: the app boots, health responds, auth gates protected
routes. Uses ASGITransport so no server/socket is needed.
"""

from __future__ import annotations

import httpx
import pytest

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


async def test_health_ok(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["engine"] == "regex"
    # request-id middleware should stamp the response
    assert resp.headers.get("X-Request-ID")


async def test_protected_route_requires_api_key(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # An arbitrary non-public path should be rejected without a key.
        resp = await client.post("/v1/analyze", json={"note": "x"})
    assert resp.status_code in (401, 404)  # 401 once routes exist; auth runs first
