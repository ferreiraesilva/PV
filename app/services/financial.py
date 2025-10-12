from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Cashflow:
    due_date: date
    amount: float
    paid_amount: float | None = None
    probability_default: float = 0.0
    probability_cancellation: float = 0.0


def present_value(
    schedule: Sequence[tuple[int, float]],
    discount_rate: float,
    periods_per_year: int = 12,
) -> float:
    rate_per_period = discount_rate / periods_per_year
    return sum(
        amount / ((1 + rate_per_period) ** period) for period, amount in schedule
    )


def payment(
    principal: float, discount_rate: float, periods: int, periods_per_year: int = 12
) -> float:
    rate_per_period = discount_rate / periods_per_year
    if rate_per_period == 0:
        return principal / periods
    factor = (rate_per_period * (1 + rate_per_period) ** periods) / (
        (1 + rate_per_period) ** periods - 1
    )
    return principal * factor


def future_value(
    principal: float, discount_rate: float, periods: int, periods_per_year: int = 12
) -> float:
    rate_per_period = discount_rate / periods_per_year
    return principal * ((1 + rate_per_period) ** periods)


def average_installment_amount(installments: Sequence[tuple[int, float]]) -> float:
    return sum(amount for _, amount in installments) / len(installments)


def mean_term_months(installments: Sequence[tuple[int, float]]) -> float:
    numerator = sum(period * amount for period, amount in installments)
    denominator = sum(amount for _, amount in installments)
    return numerator / denominator if denominator else 0.0


def calculate_simulation_metrics(
    principal: float,
    discount_rate: float,
    installments: List[tuple[int, float]],
    periods_per_year: int = 12,
) -> dict[str, float]:
    pv = present_value(installments, discount_rate, periods_per_year)
    fv = future_value(principal, discount_rate, len(installments), periods_per_year)
    pmt = payment(principal, discount_rate, len(installments), periods_per_year)
    vmp = average_installment_amount(installments)
    pmr = mean_term_months(installments)
    return {
        "present_value": round(pv, 2),
        "future_value": round(fv, 2),
        "payment": round(pmt, 2),
        "average_installment": round(vmp, 2),
        "mean_term_months": round(pmr, 2),
    }


def calculate_portfolio_value(
    cashflows: Iterable[Cashflow],
    discount_rate: float,
    default_multiplier: float = 1.0,
    cancellation_multiplier: float = 1.0,
    periods_per_year: int = 12,
) -> dict[str, float]:
    sorted_cashflows = sorted(cashflows, key=lambda c: c.due_date)
    adjusted = []
    total_expected_losses = 0.0
    for idx, cashflow in enumerate(sorted_cashflows, start=1):
        rate_per_period = discount_rate / periods_per_year
        probability_default = min(
            max(cashflow.probability_default * default_multiplier, 0.0), 1.0
        )
        probability_cancellation = min(
            max(cashflow.probability_cancellation * cancellation_multiplier, 0.0), 1.0
        )
        effective_probability = min(probability_default + probability_cancellation, 1.0)
        expected_cash = cashflow.amount * (1 - effective_probability)
        pv_component = expected_cash / ((1 + rate_per_period) ** idx)
        adjusted.append(pv_component)
        total_expected_losses += cashflow.amount - expected_cash

    vpb = sum(adjusted)
    vpl = vpb - total_expected_losses
    return {
        "gross_present_value": round(vpb, 2),
        "net_present_value": round(vpl, 2),
        "expected_losses": round(total_expected_losses, 2),
    }
