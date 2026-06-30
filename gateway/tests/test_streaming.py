"""Phase 7 — streaming boundary guard + chunk-safe rehydration."""

from __future__ import annotations

import fakeredis.aioredis
import pytest

from app.compliance.streaming import split_at_last_open, stream_rehydrate
from app.compliance.vault import RedisVault


def test_split_no_open():
    assert split_at_last_open("hello world") == ("hello world", "")


def test_split_complete_token():
    assert split_at_last_open("hi <EMAIL_1> there") == ("hi <EMAIL_1> there", "")


def test_split_holds_partial_token():
    emit, rem = split_at_last_open("hi <EMAIL_ADD")
    assert emit == "hi "
    assert rem == "<EMAIL_ADD"


@pytest.fixture
async def vault():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield RedisVault(r, ttl_seconds=60)
    await r.aclose()


async def _agen(parts):
    for p in parts:
        yield p


async def test_token_split_across_chunks_is_rehydrated(vault):
    token = await vault.get_or_create("EMAIL_ADDRESS", "a@b.com", "s1")
    assert token == "<EMAIL_ADDRESS_1>"

    # The token is split across three chunk boundaries.
    chunks = ["Reply to ", "<EMAIL_ADD", "RESS_1>", " now"]
    out = [piece async for piece in stream_rehydrate(_agen(chunks), vault, "s1")]
    joined = "".join(out)

    assert joined == "Reply to a@b.com now"
    # No partial placeholder ever leaked.
    assert "<EMAIL" not in joined
    assert "<" not in joined


async def test_stream_passthrough_without_tokens(vault):
    chunks = ["plain ", "text ", "only"]
    out = "".join([p async for p in stream_rehydrate(_agen(chunks), vault, "s1")])
    assert out == "plain text only"
