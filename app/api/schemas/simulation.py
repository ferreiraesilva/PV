from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InstallmentInput(BaseModel):
    due_date: date | None = Field(None, alias="dueDate")
    period: int | None = None
    amount: float = Field(..., gt=0)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _ensure_reference(self) -> "InstallmentInput":
        if self.due_date is None and self.period is None:
            raise ValueError("Installment must include dueDate or period")
        if self.period is not None and self.period < 0:
            raise ValueError("period must be non-negative")
        return self


class AdjustmentPayload(BaseModel):
    base_date: date = Field(..., alias="baseDate")
    index: str = Field(..., min_length=1)
    periodicity: Literal["monthly", "anniversary"]
    addon_rate: float = Field(..., ge=0, alias="addonRate")

    model_config = ConfigDict(populate_by_name=True)


class SimulationInput(BaseModel):
    principal: float = Field(..., gt=0)
    discount_rate: float = Field(..., ge=0)
    installments: List[InstallmentInput]


class SimulationPlanPayload(BaseModel):
    key: Optional[str] = Field(None, min_length=1, max_length=64)
    label: Optional[str] = None
    product_code: Optional[str] = Field(
        None, min_length=1, max_length=128, alias="productCode"
    )
    principal: float = Field(..., gt=0)
    discount_rate: float = Field(..., ge=0)
    adjustment: Optional[AdjustmentPayload] = None
    installments: List[InstallmentInput]

    model_config = ConfigDict(populate_by_name=True)


class SimulationTemplateReference(BaseModel):
    template_id: Optional[UUID] = Field(None, alias="templateId")
    product_code: Optional[str] = Field(
        None, min_length=1, max_length=128, alias="productCode"
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _validate_identifier(self) -> "SimulationTemplateReference":
        if self.template_id is None and not self.product_code:
            raise ValueError("templateId or productCode must be provided")
        return self


class SimulationBatchRequest(BaseModel):
    plans: List[SimulationPlanPayload] = Field(default_factory=list)
    templates: List[SimulationTemplateReference] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _ensure_content(self) -> "SimulationBatchRequest":
        if not self.plans and not self.templates:
            raise ValueError("At least one plan or template must be provided")
        return self


class SimulationResult(BaseModel):
    present_value: float
    present_value_adjusted: Optional[float] = None
    future_value: float
    payment: float
    average_installment: float
    mean_term_months: float


class SimulationPlanSnapshot(BaseModel):
    principal: float
    discount_rate: float
    installments: List[InstallmentInput]


class SimulationOutcome(BaseModel):
    source: Literal["input", "template"]
    plan_key: Optional[str] = None
    label: Optional[str] = None
    product_code: Optional[str] = None
    template_id: Optional[UUID] = None
    result: SimulationResult
    plan: SimulationPlanSnapshot


class SimulationBatchResponse(BaseModel):
    tenant_id: str
    outcomes: List[SimulationOutcome]


SimulationResponse = SimulationBatchResponse


class CashflowInput(BaseModel):
    due_date: date
    amount: float = Field(..., gt=0)
    probability_default: float = Field(0, ge=0, le=1)
    probability_cancellation: float = Field(0, ge=0, le=1)


class ValuationScenario(BaseModel):
    code: str
    discount_rate: float = Field(..., ge=0)
    default_multiplier: float = Field(1.0, ge=0)
    cancellation_multiplier: float = Field(1.0, ge=0)


class ValuationInput(BaseModel):
    cashflows: List[CashflowInput]
    scenarios: List[ValuationScenario]


class ScenarioResult(BaseModel):
    code: str
    gross_present_value: float
    net_present_value: float
    expected_losses: float


class ValuationResponse(BaseModel):
    tenant_id: str
    results: List[ScenarioResult]
