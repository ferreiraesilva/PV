import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(320), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    roles = Column(JSON, nullable=False, default=lambda: ["user"])
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_suspended = Column(Boolean, nullable=False, default=False)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    suspension_reason = Column(String(255), nullable=True)
    password_reset_token_hash = Column(String(255), nullable=True)
    password_reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_requested_at = Column(DateTime(timezone=True), nullable=True)
    locale = Column(String(16), nullable=False, default="en-US")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
