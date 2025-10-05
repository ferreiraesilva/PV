from datetime import date
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.routes import simulations as simulations_routes
from tests.conftest import TENANT_ID


def test_simulation_endpoint_returns_metrics(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {
        "principal": 10000,
        "discount_rate": 0.12,
        "installments": [{"period": idx + 1, "amount": 900} for idx in range(12)],
    }
    response = client.post(
        f"/v1/t/{TENANT_ID}/simulations",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == TENANT_ID
    assert len(body["outcomes"]) == 1
    outcome = body["outcomes"][0]
    assert outcome["source"] == "input"
    assert outcome["result"]["average_installment"] == 900
    assert outcome["result"]["payment"] == 888.49


def test_simulation_endpoint_uses_standard_plan_when_product_code_matches(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch,
) -> None:
    template_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    template = SimpleNamespace(
        id=template_id,
        tenant_id=UUID(TENANT_ID),
        product_code="plano-vip",
        name="Plano VIP",
        principal=5000,
        discount_rate=0.02,
        installments=[
            SimpleNamespace(period=1, amount=2500),
            SimpleNamespace(period=2, amount=2550),
        ],
    )

    class StubRepository:
        def __init__(self, session) -> None:  # noqa: D401 - stub only
            pass

        def list_by_ids(self, tenant_id, template_ids, *, only_active: bool = True):
            if template_ids and template_id in template_ids:
                return [template]
            return []

        def list_by_product_codes(self, tenant_id, product_codes, *, only_active: bool = True):
            lowered = {code.lower() for code in product_codes}
            if "plano-vip" in lowered:
                return [template]
            return []

    monkeypatch.setattr(simulations_routes, "PaymentPlanTemplateRepository", StubRepository)

    payload = {
        "plans": [
            {
                "key": "ad-hoc",
                "label": "Proposta cliente",
                "product_code": "Plano-VIP",
                "principal": 3000,
                "discount_rate": 0.03,
                "installments": [
                    {"period": 1, "amount": 1500},
                    {"period": 2, "amount": 1600},
                ],
            }
        ],
    }

    response = client.post(
        f"/v1/t/{TENANT_ID}/simulations",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["outcomes"]) == 2
    sources = {item["source"] for item in body["outcomes"]}
    assert sources == {"input", "template"}
    template_outcome = next(item for item in body["outcomes"] if item["source"] == "template")
    assert template_outcome["product_code"] == "plano-vip"
    assert template_outcome["plan"]["principal"] == 5000


def test_valuation_endpoint_returns_scenarios(client: TestClient, auth_headers: dict[str, str]) -> None:
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
    response = client.post(
        f"/v1/t/{TENANT_ID}/valuations/snapshots/snap-1/results",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == TENANT_ID
    assert len(data["results"]) == 2
    codes = {item["code"] for item in data["results"]}
    assert codes == {"base", "stress"}
