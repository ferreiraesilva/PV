from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.session import SessionLocal


@dataclass(slots=True)
class AuditRecord:
    tenant_id: UUID
    request_id: UUID
    occurred_at: datetime
    method: str
    endpoint: str
    status_code: int
    user_id: UUID | None = None
    roles: Sequence[str] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    payload_in: Mapping[str, Any] | None = None
    payload_out: Mapping[str, Any] | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    diffs: Mapping[str, Any] | None = None
    metadata: Mapping[str, Any] | None = None


class AuditService:
    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory

    def persist(self, record: AuditRecord) -> None:
        session: Session = self._session_factory()
        try:
            audit_entry = AuditLog(
                tenant_id=record.tenant_id,
                request_id=record.request_id,
                occurred_at=record.occurred_at,
                method=record.method,
                endpoint=record.endpoint,
                status_code=record.status_code,
                user_id=record.user_id,
                role=",".join(record.roles) if record.roles else None,
                ip_address=record.ip_address,
                user_agent=record.user_agent,
                payload_in=record.payload_in,
                payload_out=record.payload_out,
                resource_type=record.resource_type,
                resource_id=record.resource_id,
                diffs=record.diffs,
                metadata_json=record.metadata,
            )
            session.add(audit_entry)
            session.commit()
        finally:
            session.close()


__all__ = ["AuditRecord", "AuditService"]
