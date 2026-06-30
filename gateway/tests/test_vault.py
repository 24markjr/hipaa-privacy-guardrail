"""Phase 2 — RedisVault behaviour, against an in-memory fake Redis (with Lua)."""

from __future__ import annotations

import asyncio

import fakeredis.aioredis
import pytest

from app.compliance.vault import RedisVault


@pytest.fixture
async def redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def vault(redis):
    return RedisVault(redis, ttl_seconds=60)


async def test_same_value_same_token(vault):
    t1 = await vault.get_or_create("EMAIL", "alice@example.com", "s1")
    t2 = await vault.get_or_create("EMAIL", "alice@example.com", "s1")
    assert t1 == t2 == "<EMAIL_1>"


async def test_different_values_distinct_tokens(vault):
    t1 = await vault.get_or_create("EMAIL", "alice@example.com", "s1")
    t2 = await vault.get_or_create("EMAIL", "bob@example.com", "s1")
    assert t1 == "<EMAIL_1>"
    assert t2 == "<EMAIL_2>"


async def test_canonicalisation_collapses_case_and_space(vault):
    t1 = await vault.get_or_create("PERSON", "John  Doe", "s1")
    t2 = await vault.get_or_create("PERSON", "john doe", "s1")
    assert t1 == t2


async def test_reverse_lookup_and_mapping(vault):
    tok = await vault.get_or_create("PHONE", "+1 415 555 0100", "s1")
    assert await vault.original(tok, "s1") == "+1 415 555 0100"
    assert await vault.mapping("s1") == {tok: "+1 415 555 0100"}


async def test_session_isolation(vault):
    a = await vault.get_or_create("EMAIL", "x@y.com", "s1")
    b = await vault.get_or_create("EMAIL", "x@y.com", "s2")
    # Same token *string* (both first-in-session) but stored independently.
    assert a == b == "<EMAIL_1>"
    assert await vault.original(a, "s2") is None or await vault.original(a, "s1") == "x@y.com"
    assert await vault.mapping("s1") != {} and await vault.mapping("s2") != {}


async def test_concurrent_same_value_allocates_one_token(vault):
    # 50 concurrent first-time masks of the same value must converge to ONE token.
    results = await asyncio.gather(
        *[vault.get_or_create("AADHAAR", "1234 5678 9012", "s1") for _ in range(50)]
    )
    assert len(set(results)) == 1
    assert (await vault.stats("s1"))["total_mappings"] == 1


async def test_stats(vault):
    await vault.get_or_create("EMAIL", "a@b.com", "s1")
    await vault.get_or_create("EMAIL", "c@d.com", "s1")
    await vault.get_or_create("PAN", "ABCDE1234F", "s1")
    stats = await vault.stats("s1")
    assert stats["total_mappings"] == 3
    assert stats["by_label"] == {"EMAIL": 2, "PAN": 1}


async def test_ttl_is_set(vault, redis):
    await vault.get_or_create("EMAIL", "a@b.com", "s1")
    assert 0 < await redis.ttl("vault:s1:rev") <= 60


async def test_empty_value_rejected(vault):
    with pytest.raises(ValueError):
        await vault.get_or_create("EMAIL", "   ", "s1")


async def test_clear(vault):
    await vault.get_or_create("EMAIL", "a@b.com", "s1")
    await vault.clear("s1")
    assert await vault.mapping("s1") == {}


async def test_encryption_at_rest(redis):
    from cryptography.fernet import Fernet

    v = RedisVault(redis, ttl_seconds=60, encryption_key=Fernet.generate_key().decode())
    tok = await v.get_or_create("SSN", "123-45-6789", "s1")
    # Reverse API returns plaintext...
    assert await v.original(tok, "s1") == "123-45-6789"
    # ...but the raw stored value is ciphertext, not the SSN.
    raw = await redis.hget("vault:s1:rev", tok)
    assert "123-45-6789" not in raw
