from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional

from app.db.repositories.financial_index import FinancialIndexRepository
from app.services.financial import (
    Cashflow,
    calculate_portfolio_value,
    calculate_simulation_metrics,
)


def _calculate_months_between(start_date: date, end_date: date) -> int:
    """Calculates the number of full months between two dates for PV calculation."""
    if end_date < start_date:
        return 0
    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


class AdjustmentLogic:
    """Encapsulates the logic for applying financial index adjustments."""

    def __init__(
        self,
        base_date: date,
        index_code: str,
        periodicity: str,
        addon_rate: float,
        index_repository: FinancialIndexRepository,
        tenant_id: str,
    ):
        self.base_date = base_date
        self.index_code = index_code
        self.periodicity = periodicity
        self.addon_rate = addon_rate
        self._index_values: Dict[date, float] = {
            record.reference_date: record.value
            for record in index_repository.list_by_index_code(tenant_id, index_code)
        }

    def apply(self, periods: list[tuple[int, float]]) -> list[tuple[int, float]]:
        """Applies the adjustment to a list of installments."""
        if not self._index_values:
            # If no custom index values, fall back to a simple addon_rate adjustment
            return [
                (period, amount * ((1 + self.addon_rate) ** (period / 12)))
                for period, amount in periods
            ]

        if self.periodicity == "monthly":
            return self._apply_monthly(periods)

        if self.periodicity == "anniversary":
            return self._apply_anniversary(periods)

        raise ValueError(f"Unsupported adjustment periodicity: {self.periodicity}")

    def _apply_monthly(
        self, periods: list[tuple[int, float]]
    ) -> list[tuple[int, float]]:
        adjusted_periods = []
        for period, amount in periods:
            correction_factor = 1.0
            # Iterate from the month after base_date up to the installment's month
            for m in range(1, period + 1):
                current_month_date = self.base_date + timedelta(days=31 * m)
                reference_date = date(
                    current_month_date.year, current_month_date.month, 1
                )
                # Get index for the reference month, or default to 1.0 (no change)
                monthly_index = self._index_values.get(reference_date, 1.0)
                correction_factor *= monthly_index
            adjusted_amount = (
                amount * correction_factor * ((1 + self.addon_rate) ** (period / 12))
            )
            adjusted_periods.append((period, adjusted_amount))
        return adjusted_periods

    def _apply_anniversary(
        self, periods: list[tuple[int, float]]
    ) -> list[tuple[int, float]]:
        adjusted_periods = []
        for period, amount in periods:
            num_years_passed = period // 12
            if num_years_passed == 0:
                adjusted_periods.append((period, amount))
                continue

            correction_factor = 1.0
            for year in range(num_years_passed):
                year_start_month_offset = year * 12
                # Calculate the accumulated index for the 12 months of the current contract year
                for m in range(1, 13):
                    current_month_date = self.base_date + timedelta(
                        days=31 * (year_start_month_offset + m)
                    )
                    reference_date = date(
                        current_month_date.year, current_month_date.month, 1
                    )
                    correction_factor *= self._index_values.get(reference_date, 1.0)

            adjusted_amount = (
                amount * correction_factor * ((1 + self.addon_rate) ** num_years_passed)
            )
            adjusted_periods.append((period, adjusted_amount))
        return adjusted_periods


@dataclass
class SimulationPlan:
    periods: List[tuple[int, float]]
    principal: float
    discount_rate: float
    adjustment_logic: Optional[AdjustmentLogic] = None

    def metrics(self) -> dict[str, float]:
        metrics = calculate_simulation_metrics(
            self.principal, self.discount_rate, self.periods
        )

        if self.adjustment_logic:
            adjusted_periods = self.adjustment_logic.apply(self.periods)
            adjusted_metrics = calculate_simulation_metrics(
                self.principal, self.discount_rate, adjusted_periods
            )
            metrics["present_value_adjusted"] = adjusted_metrics["present_value"]

        return metrics


@dataclass
class PortfolioScenario:
    discount_rate: float
    default_multiplier: float
    cancellation_multiplier: float


def evaluate_portfolio(
    cashflows: List[Cashflow], scenario: PortfolioScenario
) -> dict[str, float]:
    return calculate_portfolio_value(
        cashflows,
        discount_rate=scenario.discount_rate,
        default_multiplier=scenario.default_multiplier,
        cancellation_multiplier=scenario.cancellation_multiplier,
    )
