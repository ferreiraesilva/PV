import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PaymentPlanInstallment(Base):
    __tablename__ = "payment_plan_installments"
    __table_args__ = (
        UniqueConstraint(
            "template_id", "period", name="uq_payment_plan_installments_period"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payment_plan_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    period = Column(Integer, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)

    template = relationship("PaymentPlanTemplate", back_populates="installments")
