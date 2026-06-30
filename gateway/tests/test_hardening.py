"""Hardening pass — batch vault, healthcare policy, encryption, failure contract."""

from __future__ import annotations

import asyncio

import fakeredis.aioredis
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.compliance.detectors.injection import InjectionDetector
from app.compliance.detectors.patterns_in import build_pii_detectors
from app.compliance.detectors.secrets import build_secret_detectors
from app.compliance.engine import ComplianceEngine
from app.compliance.masker import apply_masking
from app.compliance.policy import load_policy
from app.compliance.types import Action
from app.compliance.vault import RedisVault, VaultUnavailable


@pytest.fixture
async def redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


# ---- 2. Batch allocation ----
async def test_batch_allocates_in_order_and_dedupes(redis):
    vault = RedisVault(redis, ttl_seconds=60)
    tokens = await vault.get_or_create_many(
        [("EMAIL_ADDRESS", "a@b.com"), ("PERSON", "John Doe"), ("EMAIL_ADDRESS", "a@b.com")],
        "s1",
    )
    assert tokens == ["<EMAIL_ADDRESS_1>", "<PERSON_1>", "<EMAIL_ADDRESS_1>"]
    # Single-value wrapper still works and is consistent with the batch.
    assert await vault.get_or_create("EMAIL_ADDRESS", "a@b.com", "s1") == "<EMAIL_ADDRESS_1>"


async def test_batch_concurrent_same_value_one_token(redis):
    vault = RedisVault(redis, ttl_seconds=60)
    results = await asyncio.gather(
        *[vault.get_or_create_many([("AADHAAR", "4123 5678 9012")], "s1") for _ in range(40)]
    )
    assert len({r[0] for r in results}) == 1


# ---- 3. Encryption at rest ----
async def test_encryption_round_trip_via_batch(redis):
    from cryptography.fernet import Fernet

    vault = RedisVault(redis, ttl_seconds=60, encryption_key=Fernet.generate_key().decode())
    await vault.get_or_create_many([("US_SSN", "123-45-6789")], "s1")
    mapping = await vault.mapping("s1")
    assert "123-45-6789" in mapping.values()  # decrypted on read
    raw = await redis.hget("vault:s1:rev", "<US_SSN_1>")
    assert "123-45-6789" not in raw  # ciphertext at rest


# ---- 4. Failure contract ----
class _BoomRedis:
    """Stand-in whose ops raise as if Redis were unreachable."""

    def register_script(self, _):
        async def _script(*a, **k):
            raise RedisConnectionError("down")

        return _script

    async def hgetall(self, *a, **k):
        raise RedisConnectionError("down")


async def test_vault_unavailable_on_redis_error():
    vault = RedisVault(_BoomRedis(), ttl_seconds=60)
    with pytest.raises(VaultUnavailable):
        await vault.get_or_create_many([("EMAIL_ADDRESS", "a@b.com")], "s1")
    with pytest.raises(VaultUnavailable):
        await vault.mapping("s1")


# ---- 1. Healthcare policy: no OTP/bank false positives ----
async def test_healthcare_policy_does_not_scrub_clinical_numbers(redis):
    vault = RedisVault(redis, ttl_seconds=60)
    policy = load_policy("policies/healthcare.yaml")
    engine = ComplianceEngine(
        build_secret_detectors() + build_pii_detectors(), InjectionDetector(), policy, vault
    )
    result = await engine.process(
        "Patient requires a dosage of 5000 units for verification.", "s1"
    )
    assert not result.blocked
    assert "5000" in result.masked_text  # NOT masked as an OTP
    assert "IN_OTP" not in result.entity_types


def test_healthcare_policy_disables_otp_and_bank():
    policy = load_policy("policies/healthcare.yaml")
    assert policy.decide("IN_OTP").action is Action.allow
    assert policy.decide("IN_BANK_ACCOUNT").action is Action.allow
    assert policy.decide("SECRET").action is Action.block


# ---- masker uses the batch path end to end ----
async def test_apply_masking_batched(redis):
    from app.compliance.types import DetectionSource, PIIEntity

    vault = RedisVault(redis, ttl_seconds=60)
    text = "email a@b.com and name John Doe"
    ents = [
        PIIEntity("EMAIL_ADDRESS", "a@b.com", 6, 13, 1.0, DetectionSource.regex),
        PIIEntity("PERSON", "John Doe", 23, 31, 1.0, DetectionSource.regex),
    ]
    masked = await apply_masking(text, ents, vault, "s1")
    assert "a@b.com" not in masked and "John Doe" not in masked
    assert "<EMAIL_ADDRESS_1>" in masked and "<PERSON_1>" in masked
