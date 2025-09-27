import json
import time
import uuid
from typing import Any, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.audit.masking import mask_payload
from app.core.logging import logger


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        raw_body: Any = None
        if request.headers.get("content-type", "").startswith("application/json"):
            body_bytes = await request.body()
            if body_bytes:
                try:
                    raw_body = json.loads(body_bytes)
                except json.JSONDecodeError:
                    raw_body = None
            request._body = body_bytes  # type: ignore[attr-defined]

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        payload_in = mask_payload(raw_body) if raw_body is not None else None
        payload_out_raw = getattr(request.state, "audit_payload_out", None)
        payload_out = mask_payload(payload_out_raw) if payload_out_raw is not None else None
        diffs = getattr(request.state, "audit_diffs", None)

        audit_record = {
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "process_time_ms": round(process_time * 1000, 2),
            "payload_in": payload_in,
            "payload_out": payload_out,
            "diffs": diffs,
        }

        logger.bind(component="audit").info(audit_record)
        response.headers["X-Request-ID"] = request_id
        return response
