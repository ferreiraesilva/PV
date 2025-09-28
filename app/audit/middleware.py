from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from fastapi import Request
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.audit.masking import mask_payload
from app.audit.service import AuditRecord, AuditService
from app.core.logging import logger


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, audit_service: AuditService | None = None):
        super().__init__(app)
        self._audit_service = audit_service or AuditService()

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        existing_request_id = getattr(request.state, "request_id", None)
        try:
            request_uuid = uuid.UUID(str(existing_request_id)) if existing_request_id else uuid.uuid4()
        except ValueError:
            request_uuid = uuid.uuid4()
        request.state.request_id = str(request_uuid)

        raw_body: Any = None
        if request.headers.get("content-type", "").startswith("application/json"):
            body_bytes = await request.body()
            if body_bytes:
                try:
                    raw_body = json.loads(body_bytes)
                except json.JSONDecodeError:
                    raw_body = None
            request._body = body_bytes  # type: ignore[attr-defined]

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        payload_in = mask_payload(raw_body) if raw_body is not None else None
        payload_out_raw = getattr(request.state, "audit_payload_out", None)
        payload_out = mask_payload(payload_out_raw) if payload_out_raw is not None else None
        diffs_raw = getattr(request.state, "audit_diffs", None)
        diffs = mask_payload(diffs_raw) if diffs_raw is not None else None

        current_user = getattr(request.state, "current_user", None)
        tenant_identifier: str | None = None
        if current_user is not None:
            tenant_identifier = getattr(current_user, "tenant_id", None)
        if tenant_identifier is None:
            tenant_identifier = request.path_params.get("tenant_id")

        tenant_id = None
        if tenant_identifier:
            try:
                tenant_id = uuid.UUID(str(tenant_identifier))
            except ValueError:
                tenant_id = None

        actor_roles: Sequence[str] | None = getattr(request.state, "audit_actor_roles", None)
        if actor_roles and not isinstance(actor_roles, (list, tuple)):
            actor_roles = [actor_roles]  # type: ignore[list-item]
        roles = getattr(current_user, "roles", None) or actor_roles

        actor_user_id = getattr(request.state, "audit_actor_user_id", None)
        user_id_value = getattr(current_user, "user_id", None) or actor_user_id
        user_id = None
        if user_id_value:
            try:
                user_id = uuid.UUID(str(user_id_value))
            except ValueError:
                user_id = None

        resource_type = getattr(request.state, "audit_resource_type", None)
        resource_id = getattr(request.state, "audit_resource_id", None)

        audit_record_data = {
            "request_id": str(request_uuid),
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "process_time_ms": process_time_ms,
            "payload_in": payload_in,
            "payload_out": payload_out,
            "diffs": diffs,
            "resource_type": resource_type,
            "resource_id": resource_id,
        }

        logger.bind(component="audit").info(audit_record_data)
        response.headers["X-Request-ID"] = str(request_uuid)

        if tenant_id is not None:
            record = AuditRecord(
                tenant_id=tenant_id,
                request_id=request_uuid,
                occurred_at=datetime.now(timezone.utc),
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                user_id=user_id,
                roles=roles,
                ip_address=audit_record_data["client_ip"],
                user_agent=audit_record_data["user_agent"],
                payload_in=payload_in,
                payload_out=payload_out,
                resource_type=resource_type,
                resource_id=resource_id,
                diffs=diffs,
                metadata={"process_time_ms": process_time_ms},
            )
            try:
                await run_in_threadpool(self._audit_service.persist, record)
            except Exception as exc:  # pragma: no cover - defensive
                logger.bind(component="audit", error=True).exception(
                    {"message": "Failed to persist audit log", "detail": str(exc)}
                )

        return response
