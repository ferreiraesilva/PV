from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_simulation_endpoint_returns_metrics() -> None:
    payload = {
        "principal": 10000,
        "discount_rate": 0.12,
        "installments": [{"period": idx + 1, "amount": 900} for idx in range(12)],
    }
    response = client.post("/api/v1/t/demo-tenant/simulations", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == "demo-tenant"
    assert body["result"]["average_installment"] == 900
    assert body["result"]["payment"] == 888.49


def test_valuation_endpoint_returns_scenarios() -> None:
    payload = {
        "cashflows": [
            {
                "due_date": date(2026, 1, 1).isoformat(),
                "amount": 1000,
                "probability_default": 0.05,
                "probability_cancellation": 0.02,
            },
            {
                "due_date": date(2026, 2, 1).isoformat(),
                "amount": 1000,
                "probability_default": 0.08,
                "probability_cancellation": 0.03,
            },
        ],
        "scenarios": [
            {"code": "base", "discount_rate": 0.1, "default_multiplier": 1.0, "cancellation_multiplier": 1.0},
            {"code": "stress", "discount_rate": 0.12, "default_multiplier": 1.2, "cancellation_multiplier": 1.1},
        ],
    }
    response = client.post("/api/v1/t/demo-tenant/valuations/snapshots/snap-1/results", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "demo-tenant"
    assert len(data["results"]) == 2
    codes = {item["code"] for item in data["results"]}
    assert codes == {"base", "stress"}
