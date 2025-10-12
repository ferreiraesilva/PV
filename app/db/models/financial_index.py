from __future__ import annotations

from sqlalchemy import Column, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class FinancialIndexValue(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "financial_index_values"

    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    index_code = Column(String(32), nullable=False, index=True)
    reference_date = Column(Date, nullable=False)
    value = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "index_code", "reference_date", name="uq_financial_index_value"
        ),
    )

    def __repr__(self) -> str:
        return f"<FinancialIndexValue(id={self.id}, index_code='{self.index_code}', date='{self.reference_date}')>"
