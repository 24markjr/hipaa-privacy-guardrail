"""Request-context middleware: stamps every request with a request_id and
trace_id and exposes them via ``contextvars`` so any downstream code (logging,
audit, metrics) can read them without threading them through call signatures.

The contextvars technique (task-local state under asyncio) is the same approach
anon_proxy uses for its per-call masker telemetry.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

# Task-local context. Defaults make these safe to read outside a request too.
_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")

REQUEST_ID_HEADER = "X-Request-ID"
TRACE_ID_HEADER = "X-Trace-ID"


def get_request_id() -> str:
    return _request_id.get()


def get_trace_id() -> str:
    return _trace_id.get()


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Honour an inbound trace id (distributed tracing); otherwise mint one.
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid.uuid4())

        rid_token = _request_id.set(request_id)
        tid_token = _trace_id.set(trace_id)
        # Also stash on request.state for handlers that prefer explicit access.
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        finally:
            _request_id.reset(rid_token)
            _trace_id.reset(tid_token)

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
