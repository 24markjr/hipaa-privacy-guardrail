"""Active-requests gauge middleware.

The HTTP latency histogram and request counters come from the Prometheus
instrumentator; this just tracks in-flight requests as a gauge (so the dashboard
can show concurrency / load).
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.metrics import ACTIVE_REQUESTS


class ActiveRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ACTIVE_REQUESTS.inc()
        try:
            return await call_next(request)
        finally:
            ACTIVE_REQUESTS.dec()
