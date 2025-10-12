import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TenantPlanSubscription(Base):
    __tablename__ = "tenant_plan_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    activated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
