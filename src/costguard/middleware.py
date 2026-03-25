"""Rate limiting and request middleware."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per API key.

    Limits:
    - /v1/ingest: 1000 req/min (the hot path)
    - Other endpoints: 100 req/min
    """

    def __init__(self, app, ingest_rpm: int = 1000, default_rpm: int = 100):
        super().__init__(app)
        self.ingest_rpm = ingest_rpm
        self.default_rpm = default_rpm
        self._windows: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("x-api-key", "anonymous")
        path = request.url.path
        now = time.time()

        # Determine rate limit
        is_ingest = path == "/v1/ingest"
        limit = self.ingest_rpm if is_ingest else self.default_rpm
        window_key = f"{api_key}:{path}" if is_ingest else f"{api_key}:default"

        # Clean old entries (1-minute window)
        window = self._windows[window_key]
        cutoff = now - 60
        self._windows[window_key] = [t for t in window if t > cutoff]

        if len(self._windows[window_key]) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} requests/minute",
            )

        self._windows[window_key].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(limit - len(self._windows[window_key]))
        return response
