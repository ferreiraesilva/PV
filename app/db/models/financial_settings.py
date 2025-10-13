from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.db.models.base import Base, TimestampMixin


class FinancialSettings(Base, TimestampMixin):
    __tablename__ = "financial_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
        ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, index=True
    )
    periods_per_year = Column(Integer, nullable=True)
    default_multiplier = Column(Numeric(8, 4), nullable=True)
    cancellation_multiplier = Column(Numeric(8, 4), nullable=True)

    tenant = relationship("Tenant", back_populates="financial_settings")
