import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class CommercialPlan(Base):
    __tablename__ = "commercial_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_commercial_plan_tenant_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    max_users = Column(Integer, nullable=True)
    price_cents = Column(Integer, nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    is_active = Column(Boolean, nullable=False, default=True)
    billing_cycle_months = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
