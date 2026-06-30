"""Hop-by-hop header hygiene for proxying to upstream LLM providers.

adapted from anon_proxy/anon_proxy/server.py (MIT)

When we relay a client request to an upstream provider (or relay the provider's
response back), connection-management headers must not be forwarded verbatim —
``httpx`` sets its own, and forwarding the originals corrupts the transfer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

_SKIP_REQUEST_HEADERS = frozenset(
    {"host", "content-length", "content-encoding", "transfer-encoding", "connection"}
)
_SKIP_RESPONSE_HEADERS = frozenset(
    {"content-length", "content-encoding", "transfer-encoding", "connection"}
)


def forward_request_headers(headers: Mapping[str, str] | Iterable[tuple[str, str]]) -> dict[str, str]:
    items = headers.items() if isinstance(headers, Mapping) else headers
    return {k: v for k, v in items if k.lower() not in _SKIP_REQUEST_HEADERS}


def filter_response_headers(headers: Mapping[str, str] | Iterable[tuple[str, str]]) -> dict[str, str]:
    items = headers.items() if isinstance(headers, Mapping) else headers
    return {k: v for k, v in items if k.lower() not in _SKIP_RESPONSE_HEADERS}
