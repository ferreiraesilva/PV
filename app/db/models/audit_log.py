from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"postgresql_partition_by": "RANGE (occurred_at)"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    request_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(100), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    method = Column(String(10), nullable=False)
    endpoint = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=False)
    payload_in = Column(JSONB(astext_type=Text()), nullable=True)
    payload_out = Column(JSONB(astext_type=Text()), nullable=True)
    resource_type = Column(String(120), nullable=True)
    resource_id = Column(String(120), nullable=True)
    diffs = Column(JSONB(astext_type=Text()), nullable=True)
    metadata_json = Column("metadata", JSONB(astext_type=Text()), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "occurred_at": self.occurred_at,
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "role": self.role,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "method": self.method,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
        }
