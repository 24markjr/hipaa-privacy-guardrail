"""Redis-backed token vault — session-safe pseudonymisation.

Replaces the MVP's in-memory request-scoped dict with a concurrency-safe,
multi-tenant store. For each session we keep three Redis structures, all sharing
a TTL so abandoned sessions self-expire:

    vault:{session}:fwd   hash  (label\\x00canonical_value) -> token   # dedupe
    vault:{session}:rev   hash  token -> original_value               # rehydrate
    vault:{session}:cnt   hash  label -> running counter              # token ids

Design (forward/reverse maps + per-label counters, cross-value consistency,
value canonicalisation) is adapted from anon_proxy's PIIStore (MIT), re-homed
onto Redis. The encrypt-at-rest and format-preserving *concepts* are borrowed
from cloakpipe (MIT).

Allocation is done inside a single Lua script so "look up existing, else bump
counter and create" is atomic on the Redis server — two concurrent requests
masking the same new value get the *same* token, never two.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis

_WHITESPACE = re.compile(r"\s+")

# KEYS[1]=fwd KEYS[2]=rev KEYS[3]=cnt
# ARGV[1]=field ARGV[2]=label ARGV[3]=ttl ARGV[4]=original ARGV[5]=supplied_token
_ALLOC_LUA = """
local existing = redis.call('HGET', KEYS[1], ARGV[1])
if existing then
  redis.call('EXPIRE', KEYS[1], ARGV[3])
  redis.call('EXPIRE', KEYS[2], ARGV[3])
  redis.call('EXPIRE', KEYS[3], ARGV[3])
  return existing
end
local idx = redis.call('HINCRBY', KEYS[3], ARGV[2], 1)
local token
if ARGV[5] == '' then
  token = '<' .. ARGV[2] .. '_' .. idx .. '>'
else
  token = ARGV[5]
  if redis.call('HEXISTS', KEYS[2], token) == 1 then
    token = ARGV[5] .. '_' .. idx
  end
end
redis.call('HSET', KEYS[1], ARGV[1], token)
redis.call('HSET', KEYS[2], token, ARGV[4])
redis.call('EXPIRE', KEYS[1], ARGV[3])
redis.call('EXPIRE', KEYS[2], ARGV[3])
redis.call('EXPIRE', KEYS[3], ARGV[3])
return token
"""


def normalize_label(label: str) -> str:
    """Canonical label form: drop a leading ``private_`` and uppercase.

    adapted from anon_proxy/anon_proxy/mapping.py (MIT)
    """
    trimmed = label[len("private_") :] if label.startswith("private_") else label
    return trimmed.upper()


def _canonical(value: str) -> str:
    """Fold whitespace + case so "John  Doe" and "john doe" share a token."""
    return _WHITESPACE.sub(" ", value).strip().casefold()


class RedisVault:
    """Async, session-scoped pseudonymisation vault."""

    def __init__(
        self,
        redis: "Redis",
        *,
        ttl_seconds: int = 3600,
        token_style: str = "placeholder",
        encryption_key: str | None = None,
    ) -> None:
        self._redis = redis
        self._ttl = ttl_seconds
        self._token_style = token_style
        self._script = redis.register_script(_ALLOC_LUA)
        self._fernet = self._make_fernet(encryption_key)

    # ---- key helpers ----------------------------------------------------
    @staticmethod
    def _keys(session_id: str) -> tuple[str, str, str]:
        base = f"vault:{session_id}"
        return f"{base}:fwd", f"{base}:rev", f"{base}:cnt"

    @staticmethod
    def _field(label: str, value: str) -> str:
        # NUL separates label from value so neither can spoof the boundary.
        return f"{label}\x00{_canonical(value)}"

    # ---- encryption (optional, off by default) --------------------------
    @staticmethod
    def _make_fernet(key: str | None):
        if not key:
            return None
        from cryptography.fernet import Fernet  # lazy: only when enabled

        return Fernet(key)

    def _enc(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode() if self._fernet else value

    def _dec(self, value: str | None) -> str | None:
        if value is None or self._fernet is None:
            return value
        from cryptography.fernet import Fernet  # noqa: F401

        return self._fernet.decrypt(value.encode()).decode()

    # ---- format-preserving token candidates -----------------------------
    def _candidate_token(self, label: str, value: str) -> str:
        """Return a supplied token for format-preserving mode, else '' so the
        Lua script falls back to a ``<LABEL_n>`` placeholder.

        Format-preserving keeps the masked text natural for the LLM (e.g. a
        phone still *looks* like a phone). Uniqueness is still guaranteed by the
        script, which appends the counter on collision.
        """
        if self._token_style != "format_preserving":
            return ""
        up = label.upper()
        if up in {"EMAIL", "EMAIL_ADDRESS"}:
            return "redacted.user@example.invalid"
        if up in {"PHONE", "PHONE_NUMBER"}:
            digits = re.sub(r"\D", "", value)
            return "+91 55500 00000" if len(digits) >= 10 else "55500"
        return ""  # unknown label -> placeholder

    # ---- public API -----------------------------------------------------
    async def get_or_create(self, label: str, value: str, session_id: str) -> str:
        """Return the stable token for ``value`` in ``session_id`` (creating it
        atomically on first sight)."""
        if not value or not value.strip():
            raise ValueError("RedisVault.get_or_create: value must be non-empty")
        label = normalize_label(label)
        fwd, rev, cnt = self._keys(session_id)
        token = await self._script(
            keys=[fwd, rev, cnt],
            args=[
                self._field(label, value),
                label,
                self._ttl,
                self._enc(value),
                self._candidate_token(label, value),
            ],
        )
        return token

    async def original(self, token: str, session_id: str) -> str | None:
        """Reverse a single token back to its original value (or None)."""
        _, rev, _ = self._keys(session_id)
        return self._dec(await self._redis.hget(rev, token))

    async def mapping(self, session_id: str) -> dict[str, str]:
        """Full token -> original map for a session (used by the rehydrator)."""
        _, rev, _ = self._keys(session_id)
        raw = await self._redis.hgetall(rev)
        return {tok: self._dec(val) for tok, val in raw.items()}

    async def stats(self, session_id: str) -> dict:
        """Non-sensitive counts (safe to expose to the dashboard)."""
        fwd, _, cnt = self._keys(session_id)
        total = await self._redis.hlen(fwd)
        counters = await self._redis.hgetall(cnt)
        return {"total_mappings": total, "by_label": {k: int(v) for k, v in counters.items()}}

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(*self._keys(session_id))
