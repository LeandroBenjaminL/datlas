"""Authentication middleware — API key validation for protected routes.

Protects all /api/* endpoints with a configurable API key passed via
the X-API-Key header. Public routes (docs, health) are excluded.

Reads settings.API_KEY at request time so tests can toggle auth
via monkeypatch without recreating the app.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

PUBLIC_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate X-API-Key header on all non-public routes.

    Args:
        app: The FastAPI application.
        api_key: Fallback key. dispatch() reads from settings at request time.
    """

    def __init__(self, app, api_key: str = ""):
        super().__init__(app)
        self._fallback_key = api_key

    def _get_api_key(self) -> str:
        """Read the current API key: prioritize settings, fall back to init value."""
        from app.config import settings

        return settings.API_KEY or self._fallback_key

    async def dispatch(self, request: Request, call_next):
        # Allow public paths without auth
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        api_key = self._get_api_key()

        # If no API key configured, skip auth (dev mode)
        if not api_key:
            return await call_next(request)

        provided_key = request.headers.get("X-API-Key", "")

        if not provided_key:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Missing X-API-Key header. Get your API key at /docs.",
                    "docs": "/docs",
                },
            )

        if provided_key != api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Invalid API key.",
                },
            )

        return await call_next(request)
