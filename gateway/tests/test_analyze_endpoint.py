"""Phase 4 — /v1/analyze end-to-end with a fake provider and fake Redis.

Dependency overrides inject test doubles so no network, real Redis, or Gemini
key is needed. The fake provider echoes the masked text back (as a real model
would, when told to preserve <TOKEN> placeholders), letting us assert the full
mask -> LLM -> rehydrate round-trip.
"""

from __future__ import annotations

import fakeredis.aioredis
import httpx
import pytest

from app.compliance.engine import ComplianceEngine
from app.compliance.detectors.injection import InjectionDetector
from app.compliance.detectors.patterns_in import build_pii_detectors
from app.compliance.detectors.secrets import build_secret_detectors
from app.compliance.policy import Policy
from app.compliance.types import Action
from app.compliance.vault import RedisVault
from app.dependencies import (
    audit_dep,
    engine_dep,
    history_sink_dep,
    provider_dep,
    vault_dep,
)
from app.main import create_app
from app.providers.base import BaseLLMProvider


class _FakeAudit:
    def __init__(self) -> None:
        self.records = []

    def log(self, record) -> None:
        self.records.append(record)


class EchoProvider(BaseLLMProvider):
    name = "echo"

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        # Echo back the (masked) clinical note portion of the prompt.
        return prompt.split("Clinical Note:\n\n", 1)[-1].strip()


@pytest.fixture
async def client_and_vault():
    app = create_app()
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    vault = RedisVault(redis, ttl_seconds=60)

    def make_engine(policy: Policy) -> ComplianceEngine:
        detectors = build_secret_detectors() + build_pii_detectors()
        return ComplianceEngine(detectors, InjectionDetector(), policy, vault)

    app.state._make_engine = make_engine  # so tests can swap the policy
    app.state._vault = vault

    app.dependency_overrides[vault_dep] = lambda: vault
    app.dependency_overrides[provider_dep] = lambda: EchoProvider()
    app.dependency_overrides[audit_dep] = lambda: _FakeAudit()
    app.dependency_overrides[history_sink_dep] = lambda: _FakeAudit()
    # default: mask everything
    app.dependency_overrides[engine_dep] = lambda: make_engine(
        Policy(name="t", profile="g", default_action=Action.mask)
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-API-Key": "dev-local-key"}
    ) as c:
        yield c, app, make_engine
    await redis.aclose()


async def test_analyze_masks_and_rehydrates(client_and_vault):
    client, _, _ = client_and_vault
    resp = await client.post(
        "/v1/analyze", json={"note": "Patient email is jane@clinic.com", "session_id": "s1"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "jane@clinic.com" not in body["maskedText"]
    assert body["piiCount"] >= 1
    # Echo provider returned the masked note; rehydration restores the email.
    assert "jane@clinic.com" in body["finalSummary"]


async def test_analyze_requires_auth(client_and_vault):
    client, _, _ = client_and_vault
    resp = await client.post("/v1/analyze", json={"note": "x"}, headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


async def test_analyze_blocks_per_policy(client_and_vault):
    client, app, make_engine = client_and_vault
    app.dependency_overrides[engine_dep] = lambda: make_engine(
        Policy(
            name="dpdp", profile="fintech", default_action=Action.mask,
            by_label={"IN_AADHAAR": Action.block},
        )
    )
    resp = await client.post(
        "/v1/analyze", json={"note": "Aadhaar 4123 5678 9012", "session_id": "s2"}
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["blocked"] is True
    assert "IN_AADHAAR" in body["reason"]
