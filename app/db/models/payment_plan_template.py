import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PaymentPlanTemplate(Base):
    __tablename__ = "payment_plan_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_code", name="uq_payment_plan_templates_product"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    product_code = Column(String(128), nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)
    principal = Column(Numeric(18, 4), nullable=False)
    discount_rate = Column(Numeric(10, 6), nullable=False, default=0)
    metadata_json = Column("metadata", JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    installments = relationship(
        "PaymentPlanInstallment",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="PaymentPlanInstallment.period",
        lazy="joined",
    )
