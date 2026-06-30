"""Shared async HTTP client and upstream request helper.

The client is created once per process in the app lifespan (see
``app/main.py``) and stored on ``app.state`` so connection pooling actually
works — creating an ``httpx.AsyncClient`` per request defeats keep-alive and is
a common performance bug.

``upstream_request`` adds 429 retry with Retry-After / exponential backoff.

adapted from anon_proxy/anon_proxy/server.py (MIT)
"""

from __future__ import annotations

import asyncio
import random

import httpx


def build_async_client(timeout_seconds: float) -> httpx.AsyncClient:
    """Build the shared client. Generous read timeout (LLMs are slow), short connect."""
    return httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds, connect=10.0))


def _parse_retry_after(headers: httpx.Headers) -> float | None:
    val = headers.get("retry-after")
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None


async def upstream_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
    params: dict | None = None,
    stream: bool = False,
    max_retries: int = 3,
) -> httpx.Response:
    """Send a request, retrying on HTTP 429.

    Honours the upstream ``Retry-After`` header; falls back to exponential
    backoff with jitter. Returns the final response (even if still 429) once
    retries are exhausted.
    """
    for attempt in range(max_retries + 1):
        req = client.build_request(method, url, content=content, headers=headers, params=params)
        resp = await client.send(req, stream=stream)
        if resp.status_code != 429 or attempt == max_retries:
            return resp

        wait = _parse_retry_after(resp.headers)
        if wait is None:
            wait = (2**attempt) * (0.5 + random.random() * 0.5)
        if stream:
            await resp.aread()
        await resp.aclose()
        await asyncio.sleep(wait)

    raise RuntimeError("upstream_request: exhausted retries")  # unreachable
