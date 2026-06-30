"""Masking & rehydration against the Redis vault.

Substitution strategy adapted from anon_proxy/anon_proxy/masker.py (MIT):
tokens are allocated left-to-right (so the leftmost entity gets the lowest
index, matching reading order) but applied right-to-left so earlier spans'
offsets stay valid as the text is rewritten.

The vault is async, so these are coroutines (anon_proxy's store is sync).
"""

from __future__ import annotations

import json
import re

from app.compliance.types import PIIEntity
from app.compliance.vault import RedisVault


async def apply_masking(
    text: str, entities: list[PIIEntity], vault: RedisVault, session_id: str
) -> str:
    """Replace each entity with a vault token. Entities must be non-overlapping
    (run ``resolve_overlaps`` first)."""
    if not entities:
        return text
    ordered = sorted(entities, key=lambda e: e.start)
    # One batched round trip to the vault instead of one per entity.
    tokens = await vault.get_or_create_many(
        [(e.label, e.text) for e in ordered], session_id
    )
    masked = text
    for e, token in zip(reversed(ordered), reversed(tokens)):
        masked = masked[: e.start] + token + masked[e.end :]
    return masked


def _build_token_regex(tokens: list[str]) -> re.Pattern[str] | None:
    if not tokens:
        return None
    # Longest-first so "<X_1>" can't shadow "<X_10>".
    return re.compile("|".join(re.escape(t) for t in sorted(tokens, key=len, reverse=True)))


async def rehydrate(text: str, vault: RedisVault, session_id: str) -> str:
    """Restore original values for every token found in ``text``."""
    mapping = await vault.mapping(session_id)
    rx = _build_token_regex(list(mapping))
    if rx is None:
        return text
    return rx.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)


async def rehydrate_json(text: str, vault: RedisVault, session_id: str) -> str:
    """Rehydrate tokens that live inside a JSON string context.

    Restored values are JSON-escaped so an original containing quotes/backslashes
    doesn't break the surrounding JSON (used for streaming JSON deltas).
    adapted from anon_proxy unmask_json (MIT).
    """
    mapping = await vault.mapping(session_id)
    rx = _build_token_regex(list(mapping))
    if rx is None:
        return text

    def repl(m: re.Match[str]) -> str:
        original = mapping.get(m.group(0))
        return json.dumps(original)[1:-1] if original is not None else m.group(0)

    return rx.sub(repl, text)
