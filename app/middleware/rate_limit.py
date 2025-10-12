from __future__ import annotations

import asyncio
import time
from typing import Any, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.errors import ErrorResponse
from app.core.logging import logger
from app.observability.metrics import RATE_LIMIT_COUNTER


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        limit: int,
        window_seconds: int,
        excluded_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.excluded_paths = excluded_paths or set()
        self._buckets: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    def reset(self) -> None:
        self._buckets.clear()

    def _make_key(self, request: Request) -> str:
        client_ip = request.client.host if request.client else "anonymous"
        return f"{client_ip}:{request.url.path}"

    async def dispatch(self, request: Request, call_next: Callable[..., Any]):
        if request.method == "OPTIONS" or request.url.path in self.excluded_paths:
            return await call_next(request)

        key = self._make_key(request)
        now = time.time()
        async with self._lock:
            count, reset_at = self._buckets.get(key, (0, now + self.window_seconds))
            if now > reset_at:
                count = 0
                reset_at = now + self.window_seconds
            count += 1
            self._buckets[key] = (count, reset_at)
            remaining = max(self.limit - count, 0)
            limit_exceeded = count > self.limit

        if limit_exceeded:
            retry_after = max(int(reset_at - now), 1)
            RATE_LIMIT_COUNTER.labels(endpoint=request.url.path).inc()
            logger.bind(
                component="rate_limit",
                request_id=getattr(request.state, "request_id", None),
            ).warning(
                {
                    "message": "Rate limit exceeded",
                    "key": key,
                    "retry_after": retry_after,
                }
            )
            payload = ErrorResponse(
                code="rate_limit_exceeded",
                message="Too many requests",
                detail={"retry_after": retry_after},
                request_id=getattr(request.state, "request_id", None),
            )
            response = JSONResponse(status_code=429, content=payload.model_dump())
            response.headers.update(
                {
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                }
            )
            return response

        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Limit", str(self.limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        response.headers.setdefault("X-RateLimit-Reset", str(int(reset_at)))
        return response
