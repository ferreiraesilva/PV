from __future__ import annotations

from collections.abc import Iterable
from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import PaymentPlanTemplate


class PaymentPlanTemplateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_ids(self, tenant_id: UUID, template_ids: Iterable[UUID], *, only_active: bool = True) -> list[PaymentPlanTemplate]:
        ids: Sequence[UUID] = tuple(template_ids)
        if not ids:
            return []
        stmt = select(PaymentPlanTemplate).where(
            PaymentPlanTemplate.tenant_id == tenant_id,
            PaymentPlanTemplate.id.in_(ids),
        )
        if only_active:
            stmt = stmt.where(PaymentPlanTemplate.is_active.is_(True))
        result = self.session.execute(stmt.order_by(PaymentPlanTemplate.product_code)).unique()
        return list(result.scalars())

    def list_by_product_codes(self, tenant_id: UUID, product_codes: Iterable[str], *, only_active: bool = True) -> list[PaymentPlanTemplate]:
        normalized = tuple(code.strip().lower() for code in product_codes if code and code.strip())
        if not normalized:
            return []
        stmt = select(PaymentPlanTemplate).where(
            PaymentPlanTemplate.tenant_id == tenant_id,
            func.lower(PaymentPlanTemplate.product_code).in_(normalized),
        )
        if only_active:
            stmt = stmt.where(PaymentPlanTemplate.is_active.is_(True))
        result = self.session.execute(stmt.order_by(PaymentPlanTemplate.product_code)).unique()
        return list(result.scalars())

    def get_by_id(self, tenant_id: UUID, template_id: UUID) -> PaymentPlanTemplate | None:
        stmt = select(PaymentPlanTemplate).where(
            PaymentPlanTemplate.tenant_id == tenant_id,
            PaymentPlanTemplate.id == template_id,
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()
