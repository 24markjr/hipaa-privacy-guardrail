"""Streaming-safe rehydration for SSE / voice pipelines.

The hard part of streaming a masked LLM response is that a placeholder token can
be split across two stream chunks ("...<EMAIL_ADD" | "RESS_1>..."). If we
rehydrated each chunk independently we'd either leak a half-token to the client
or fail to match it. ``split_at_last_open`` holds back everything from the last
unterminated ``<`` until its closing ``>`` arrives, so we only ever rehydrate
complete tokens.

split_at_last_open adapted from anon_proxy/anon_proxy/adapters/_streaming.py (MIT).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.compliance.masker import _build_token_regex
from app.compliance.vault import RedisVault


def split_at_last_open(buf: str) -> tuple[str, str]:
    """Split into (emittable, remainder).

    The remainder is the substring from the last unterminated ``<`` onward — a
    possibly-incomplete placeholder that must wait for the next chunk. If there's
    no ``<``, or the last ``<`` already has a closing ``>``, the whole buffer is
    emittable.
    """
    last_open = buf.rfind("<")
    if last_open == -1 or ">" in buf[last_open:]:
        return buf, ""
    return buf[:last_open], buf[last_open:]


async def stream_rehydrate(
    chunks: AsyncIterator[str], vault: RedisVault, session_id: str
) -> AsyncIterator[str]:
    """Rehydrate tokens in a stream of text chunks, never leaking a partial token.

    The session's token map is fetched once up-front — it was fully populated
    when the *request* was masked, before the response started streaming.
    """
    mapping = await vault.mapping(session_id)
    rx = _build_token_regex(list(mapping))

    def restore(text: str) -> str:
        if rx is None or not text:
            return text
        return rx.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)

    buffer = ""
    async for chunk in chunks:
        if not chunk:
            continue
        buffer += chunk
        emittable, buffer = split_at_last_open(buffer)
        if emittable:
            yield restore(emittable)
    if buffer:
        yield restore(buffer)
