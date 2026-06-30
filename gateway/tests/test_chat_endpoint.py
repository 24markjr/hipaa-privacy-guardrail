"""Phase 7 — /v1/chat/completions: masking + non-stream + streaming SSE + block."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import fakeredis.aioredis
import httpx
import pytest

from app.compliance.detectors.injection import InjectionDetector
from app.compliance.detectors.patterns_in import build_pii_detectors
from app.compliance.detectors.secrets import build_secret_detectors
from app.compliance.engine import ComplianceEngine
from app.compliance.policy import Policy
from app.compliance.types import Action
from app.compliance.vault import RedisVault
from app.dependencies import audit_dep, engine_dep, provider_dep, vault_dep
from app.main import create_app
from app.providers.base import BaseLLMProvider


class _FakeAudit:
    def log(self, record) -> None:  # noqa: D401
        pass


class ChunkEchoProvider(BaseLLMProvider):
    """Echoes the (masked) prompt back, streaming in tiny chunks so tokens get
    split across boundaries — exercising the boundary guard."""

    name = "chunkecho"

    async def complete(self, prompt: str, *, model: str | None = None) -> str:
        return prompt

    async def stream(self, prompt: str, *, model: str | None = None) -> AsyncIterator[str]:
        for i in range(0, len(prompt), 3):
            yield prompt[i : i + 3]


def _engine(vault, policy):
    detectors = build_secret_detectors() + build_pii_detectors()
    return ComplianceEngine(detectors, InjectionDetector(), policy, vault)


@pytest.fixture
async def ctx():
    app = create_app()
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    vault = RedisVault(redis, ttl_seconds=60)

    app.dependency_overrides[vault_dep] = lambda: vault
    app.dependency_overrides[provider_dep] = lambda: ChunkEchoProvider()
    app.dependency_overrides[audit_dep] = lambda: _FakeAudit()
    app.dependency_overrides[engine_dep] = lambda: _engine(
        vault, Policy(name="t", profile="g", default_action=Action.mask)
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", headers={"X-API-Key": "dev-local-key"}
    ) as c:
        yield c, app, vault
    await redis.aclose()


async def test_chat_non_streaming_masks_and_rehydrates(ctx):
    client, _, _ = ctx
    resp = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "email me at a@b.com"}], "session_id": "s1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "a@b.com" not in body["maskedPrompt"]  # masked going out
    assert "a@b.com" in body["choices"][0]["message"]["content"]  # rehydrated coming back


async def test_chat_streaming_sse_rehydrates_without_leak(ctx):
    client, _, _ = ctx
    resp = await client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "send to a@b.com please"}],
            "session_id": "s2",
            "stream": True,
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    content = ""
    saw_done = False
    for line in resp.text.splitlines():
        if not line.startswith("data: "):
            continue
        data = line.removeprefix("data: ")
        if data == "[DONE]":
            saw_done = True
            continue
        content += json.loads(data)["choices"][0]["delta"]["content"]

    assert saw_done
    assert "a@b.com" in content       # rehydrated across chunk boundaries
    assert "<EMAIL" not in content    # no partial/whole token leaked


async def test_chat_blocks_per_policy(ctx):
    client, app, vault = ctx
    app.dependency_overrides[engine_dep] = lambda: _engine(
        vault,
        Policy(name="dpdp", profile="f", default_action=Action.mask,
               by_label={"IN_AADHAAR": Action.block}),
    )
    resp = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Aadhaar 4123 5678 9012"}]},
    )
    assert resp.status_code == 422
    assert resp.json()["blocked"] is True
