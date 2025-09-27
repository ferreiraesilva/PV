from datetime import date
from typing import List

from pydantic import BaseModel, Field


class InstallmentInput(BaseModel):
    period: int = Field(..., ge=1)
    amount: float = Field(..., gt=0)


class SimulationInput(BaseModel):
    principal: float = Field(..., gt=0)
    discount_rate: float = Field(..., ge=0)
    installments: List[InstallmentInput]


class SimulationResult(BaseModel):
    present_value: float
    future_value: float
    payment: float
    average_installment: float
    mean_term_months: float


class SimulationResponse(BaseModel):
    tenant_id: str
    plan: SimulationInput
    result: SimulationResult


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
