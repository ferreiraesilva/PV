from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FinancialSettingsBase(BaseModel):
    periods_per_year: int | None = Field(
        None, description="Number of periods per year for interest calculation"
    )
    default_multiplier: float | None = Field(
        None, description="Multiplier for the default probability"
    )
    cancellation_multiplier: float | None = Field(
        None, description="Multiplier for the cancellation probability"
    )


class FinancialSettingsCreate(FinancialSettingsBase):
    pass


class FinancialSettingsUpdate(FinancialSettingsBase):
    pass


class FinancialSettings(FinancialSettingsBase):
    tenant_id: str

    model_config = ConfigDict(from_attributes=True)
