from __future__ import annotations

import uuid
from typing import Any, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[..., Any]):
        request_id = getattr(request.state, "request_id", None)
        try:
            request_uuid = uuid.UUID(str(request_id)) if request_id else uuid.uuid4()
        except ValueError:
            request_uuid = uuid.uuid4()
        request.state.request_id = str(request_uuid)

        with logger.contextualize(request_id=str(request_uuid), path=request.url.path, method=request.method):
            response = await call_next(request)
        return response
