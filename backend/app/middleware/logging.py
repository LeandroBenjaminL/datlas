"""
Request ID middleware for Datlas.

Injects an X-Request-ID header into every response and makes
the request ID available via the logging context.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging import request_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has a traceable ID.

    - Reads X-Request-ID from the incoming request (if provided).
    - Generates a new UUIDv4 if none was sent.
    - Sets the request_id in the logging context.
    - Adds X-Request-ID to the response headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use existing request ID or generate a new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        request_id_ctx.set(request_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
