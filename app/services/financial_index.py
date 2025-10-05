from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas.financial_index import IndexValueInput
from app.db.models.financial_index import FinancialIndexValue
from app.db.repositories.financial_index import FinancialIndexRepository
from app.services.administration import ActingUser, PermissionDeniedError


class FinancialIndexService:
    def __init__(self, db: Session):
        self._repository = FinancialIndexRepository(db)

    def list_values(self, acting_user: ActingUser, tenant_id: UUID, index_code: str) -> list[FinancialIndexValue]:
        if not acting_user.is_superuser() and acting_user.tenant_id != tenant_id:
            raise PermissionDeniedError("User cannot access indexes from another tenant.")
        return self._repository.list_by_index_code(tenant_id, index_code)

    def create_or_update_values(
        self, acting_user: ActingUser, tenant_id: UUID, index_code: str, values: list[IndexValueInput]
    ) -> list[FinancialIndexValue]:
        if not acting_user.is_superuser() and not acting_user.is_tenant_admin_for(tenant_id):
            raise PermissionDeniedError("Only tenant administrators can manage index values.")

        if not values:
            return []

        return self._repository.create_or_update_values(tenant_id, index_code, values)