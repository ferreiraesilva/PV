from datetime import date

from app.services.financial import Cashflow, calculate_portfolio_value, calculate_simulation_metrics, payment, present_value


def test_present_value_matches_expected() -> None:
    schedule = [(0, 1000), (12, 1000), (24, 1000)]
    pv = present_value(schedule, discount_rate=0.12)
    assert round(pv, 2) == 2675.02


def test_payment_annuity() -> None:
    amount = 10000
    pmt = payment(amount, discount_rate=0.12, periods=12)
    assert round(pmt, 2) == 888.49


def test_simulation_metrics() -> None:
    installments = [(month, 900) for month in range(1, 13)]
    metrics = calculate_simulation_metrics(
        principal=10000,
        discount_rate=0.12,
        installments=installments,
    )
    assert metrics["average_installment"] == 900
    assert round(metrics["payment"], 2) == 888.49


def test_portfolio_value_handles_default_and_cancellation() -> None:
    cashflows = [
        Cashflow(due_date=date(2026, 1, 1), amount=1000, probability_default=0.05, probability_cancellation=0.02),
        Cashflow(due_date=date(2026, 2, 1), amount=1000, probability_default=0.08, probability_cancellation=0.03),
        Cashflow(due_date=date(2026, 3, 1), amount=1500, probability_default=0.1, probability_cancellation=0.02),
    ]
    result = calculate_portfolio_value(cashflows, discount_rate=0.15, default_multiplier=1.1, cancellation_multiplier=1.0)
    assert result["gross_present_value"] > result["net_present_value"]
    assert result["expected_losses"] > 0
