from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from sqlalchemy.orm import Session

from app.api.schemas.financial_settings import FinancialSettings
from app.core.config import get_settings
from app.db.repositories.financial_settings import FinancialSettingsRepository


class FinancialSettingsService:
    def __init__(self, db: Session):
        self.repository = FinancialSettingsRepository(db)

    def get_financial_settings(self, tenant_id: UUID) -> FinancialSettings:
        settings = self.repository.get_by_tenant_id(tenant_id)
        if settings:
            return FinancialSettings(
                tenant_id=str(settings.tenant_id),
                periods_per_year=settings.periods_per_year,
                default_multiplier=settings.default_multiplier,
                cancellation_multiplier=settings.cancellation_multiplier,
            )

        default_settings = get_settings()
        return FinancialSettings(
            tenant_id=str(tenant_id),
            periods_per_year=default_settings.periods_per_year,
            default_multiplier=default_settings.default_multiplier,
            cancellation_multiplier=default_settings.cancellation_multiplier,
        )


@lru_cache()
def get_financial_settings_service(db: Session) -> FinancialSettingsService:
    return FinancialSettingsService(db)
