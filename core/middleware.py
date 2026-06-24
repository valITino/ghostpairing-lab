"""
Rate limiting, request ID, error handling, and security header middleware.
"""
import time
import uuid
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import (
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter keyed by client IP."""

    def __init__(self, app, max_requests: int = RATE_LIMIT_REQUESTS,
                 window: int = RATE_LIMIT_WINDOW):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._clients: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        self._clients[client_ip] = [
            t for t in self._clients[client_ip] if now - t < self.window
        ]

        if len(self._clients[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Slow down."},
                headers={
                    "Retry-After": str(self.window),
                    "X-RateLimit-Limit": str(self.max_requests),
                },
            )

        self._clients[client_ip].append(now)
        return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID header and attach to request state."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add basic security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler — returns safe JSON, never leaks stack traces."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            from core.logging_config import get_logger
            logger = get_logger(__name__)
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(f"Unhandled error [request_id={request_id}]: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                },
            )
