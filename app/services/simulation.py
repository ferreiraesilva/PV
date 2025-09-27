from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from app.services.financial import Cashflow, calculate_portfolio_value, calculate_simulation_metrics


@dataclass
class SimulationPlan:
    periods: List[tuple[int, float]]
    principal: float
    discount_rate: float

    def metrics(self) -> dict[str, float]:
        return calculate_simulation_metrics(self.principal, self.discount_rate, self.periods)


@dataclass
class PortfolioScenario:
    discount_rate: float
    default_multiplier: float
    cancellation_multiplier: float


def evaluate_portfolio(cashflows: List[Cashflow], scenario: PortfolioScenario) -> dict[str, float]:
    return calculate_portfolio_value(
        cashflows,
        discount_rate=scenario.discount_rate,
        default_multiplier=scenario.default_multiplier,
        cancellation_multiplier=scenario.cancellation_multiplier,
    )
