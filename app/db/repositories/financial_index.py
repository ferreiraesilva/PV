from __future__ import annotations

from datetime import date
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas.financial_index import IndexValueInput
from app.db.models.financial_index import FinancialIndexValue


class FinancialIndexRepository:
    def __init__(self, db: Session):
        self._db = db

    def list_by_index_code(self, tenant_id: UUID, index_code: str) -> list[FinancialIndexValue]:
        return (
            self._db.query(FinancialIndexValue)
            .filter_by(tenant_id=tenant_id, index_code=index_code)
            .order_by(FinancialIndexValue.reference_date)
            .all()
        )

    def create_or_update_values(
        self, tenant_id: UUID, index_code: str, values: list[IndexValueInput]
    ) -> list[FinancialIndexValue]:
        reference_dates = [v.reference_date for v in values]
        existing_records = self._db.query(FinancialIndexValue).filter(
            FinancialIndexValue.tenant_id == tenant_id,
            FinancialIndexValue.index_code == index_code,
            FinancialIndexValue.reference_date.in_(reference_dates),
        ).all()
        existing_map = {record.reference_date: record for record in existing_records}

        for value_input in values:
            if record := existing_map.get(value_input.reference_date):
                record.value = value_input.value
            else:
                new_record = FinancialIndexValue(tenant_id=tenant_id, index_code=index_code, **value_input.model_dump())
                self._db.add(new_record)

        return self.list_by_index_code(tenant_id, index_code)