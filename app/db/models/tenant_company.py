import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TenantCompany(Base):
    __tablename__ = "tenant_companies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "tax_id", name="uq_tenant_companies_tax_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255), nullable=True)
    tax_id = Column(String(32), nullable=False)
    billing_email = Column(String(320), nullable=False)
    billing_phone = Column(String(32), nullable=True)
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(128), nullable=False)
    state = Column(String(64), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(64), nullable=False, default="BR")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
