from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas.financial_settings import (
    FinancialSettingsCreate,
    FinancialSettingsUpdate,
)
from app.db.models.financial_settings import FinancialSettings


class FinancialSettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_tenant_id(
        self, tenant_id: UUID | str
    ) -> FinancialSettings | None:
        tenant_uuid = self._normalize_tenant_id(tenant_id)
        return (
            self.db.query(FinancialSettings)
            .filter(FinancialSettings.tenant_id == tenant_uuid)
            .first()
        )

    def create(
        self, tenant_id: UUID | str, obj_in: FinancialSettingsCreate
    ) -> FinancialSettings:
        tenant_uuid = self._normalize_tenant_id(tenant_id)
        payload = self._dump_model(obj_in)
        db_obj = FinancialSettings(**payload, tenant_id=tenant_uuid)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: FinancialSettings,
        obj_in: FinancialSettingsUpdate | dict[str, Any],
    ) -> FinancialSettings:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = self._dump_model(obj_in, exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    @staticmethod
    def _dump_model(model: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(model, "model_dump"):
            return model.model_dump(exclude_unset=exclude_unset)
        if hasattr(model, "dict"):
            return model.dict(exclude_unset=exclude_unset)
        raise TypeError(f"Unsupported model type: {type(model)!r}")

    @staticmethod
    def _normalize_tenant_id(tenant_id: UUID | str) -> UUID:
        if isinstance(tenant_id, UUID):
            return tenant_id
        return UUID(str(tenant_id))
