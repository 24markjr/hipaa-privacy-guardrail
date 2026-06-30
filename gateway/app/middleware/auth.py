"""Authentication middleware.

Rejects unauthenticated requests *before* any compliance/LLM work runs. When
``AUTH_MODE`` is not ``none``, a request is accepted if it carries **either**:

    * a valid doctor JWT in ``Authorization: Bearer <token>`` (sets request.state.user_id), or
    * a valid ``X-API-Key`` (service/admin clients).

This lets the doctor app use JWTs while the admin dashboard / service callers
keep using API keys. Public paths (health, metrics, docs, auth login/register,
dashboard) are always exempt.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from app.auth.security import decode_token
from app.config import AuthMode, Settings

_PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
        "/dashboard",
        "/v1/auth/login",
        "/v1/auth/register",
    }
)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._api_keys = frozenset(settings.api_keys)

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        if self._settings.auth_mode is AuthMode.none:
            request.state.principal = "anonymous"
            request.state.user_id = None
            return await call_next(request)

        # 1. Bearer JWT (doctor app).
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            claims = decode_token(
                token,
                secret=self._settings.jwt_secret,
                algorithm=self._settings.jwt_algorithm,
            )
            if claims is None:
                return self._unauthorized("invalid or expired token")
            request.state.user_id = claims.get("sub")
            request.state.principal = f"user:{claims.get('sub')}"
            request.state.jwt_claims = claims
            return await call_next(request)

        # 2. API key (service/admin).
        key = request.headers.get("X-API-Key")
        if key and key in self._api_keys:
            request.state.user_id = None
            request.state.principal = f"apikey:{key[:4]}…"
            return await call_next(request)

        return self._unauthorized("missing or invalid credentials")

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse({"error": "unauthorized", "detail": detail}, status_code=401)
