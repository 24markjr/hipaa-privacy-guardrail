"""Structured JSON access-log middleware.

Emits one JSON line per request with the request_id/trace_id (from
RequestContextMiddleware), method, path, status, and wall-clock duration.
Structured logs are what feed log aggregators in production — one line, machine
parseable, correlatable by request_id.
"""

from __future__ import annotations

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.middleware.request_context import get_request_id, get_trace_id

_logger = logging.getLogger("gateway.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            _logger.info(
                json.dumps(
                    {
                        "request_id": get_request_id(),
                        "trace_id": get_trace_id(),
                        "method": request.method,
                        "path": request.url.path,
                        "status": status,
                        "duration_ms": round(duration_ms, 2),
                        "client": request.client.host if request.client else None,
                    }
                )
            )
