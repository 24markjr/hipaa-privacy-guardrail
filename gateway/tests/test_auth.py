"""P1 — auth: register/login/me, dual-credential middleware, security helpers."""

from __future__ import annotations

import httpx
import pytest

from app.auth.security import hash_password, verify_password
from app.db.users import InMemoryUserRepository
from app.dependencies import users_dep
from app.main import create_app


def test_password_hash_roundtrip():
    h = hash_password("s3cretpassword")
    assert h != "s3cretpassword"
    assert verify_password("s3cretpassword", h)
    assert not verify_password("wrong", h)


@pytest.fixture
def app():
    app = create_app()
    app.dependency_overrides[users_dep] = lambda: InMemoryUserRepository()
    # Share one repo instance across the app for the test session.
    repo = InMemoryUserRepository()
    app.dependency_overrides[users_dep] = lambda: repo
    return app


async def _client(app):
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_register_login_me_flow(app):
    async with await _client(app) as c:
        r = await c.post(
            "/v1/auth/register",
            json={"email": "doc@clinic.com", "password": "supersecret1", "name": "Dr. A"},
        )
        assert r.status_code == 201
        token = r.json()["access_token"]
        assert token

        # Duplicate registration is rejected.
        r2 = await c.post(
            "/v1/auth/register", json={"email": "doc@clinic.com", "password": "supersecret1"}
        )
        assert r2.status_code == 409

        # Login works and returns a token.
        r3 = await c.post(
            "/v1/auth/login", json={"email": "doc@clinic.com", "password": "supersecret1"}
        )
        assert r3.status_code == 200
        bearer = r3.json()["access_token"]

        # /me requires the bearer token.
        r4 = await c.get("/v1/auth/me", headers={"Authorization": f"Bearer {bearer}"})
        assert r4.status_code == 200
        assert r4.json()["email"] == "doc@clinic.com"


async def test_login_wrong_password(app):
    async with await _client(app) as c:
        await c.post(
            "/v1/auth/register", json={"email": "x@y.com", "password": "supersecret1"}
        )
        r = await c.post("/v1/auth/login", json={"email": "x@y.com", "password": "nope"})
        assert r.status_code == 401


async def test_me_requires_auth(app):
    async with await _client(app) as c:
        r = await c.get("/v1/auth/me")
    assert r.status_code == 401


async def test_protected_route_accepts_api_key_or_jwt(app):
    # API key still works on a protected route (no JWT needed).
    async with await _client(app) as c:
        reg = await c.post(
            "/v1/auth/register", json={"email": "z@y.com", "password": "supersecret1"}
        )
        jwt = reg.json()["access_token"]
        # JWT path
        r_jwt = await c.get("/v1/auth/me", headers={"Authorization": f"Bearer {jwt}"})
        assert r_jwt.status_code == 200
        # API-key path on a different protected endpoint
        r_key = await c.get("/v1/admin/stats", headers={"X-API-Key": "dev-local-key"})
        assert r_key.status_code == 200
