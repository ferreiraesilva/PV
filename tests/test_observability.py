from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.conftest import TENANT_ID

settings = get_settings()


def _simulation_payload() -> dict[str, object]:
    return {
        "principal": 10000,
        "discount_rate": 0.12,
        "installments": [{"period": idx + 1, "amount": 900} for idx in range(12)],
    }


def test_rate_limit_blocks_excessive_requests(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    path = f"/v1/t/{TENANT_ID}/simulations"
    for _ in range(settings.rate_limit_requests):
        response = client.post(path, json=_simulation_payload(), headers=auth_headers)
        assert response.status_code == 200
    blocked = client.post(path, json=_simulation_payload(), headers=auth_headers)
    assert blocked.status_code == 429
    data = blocked.json()
    assert data["code"] == "rate_limit_exceeded"
    assert data["message"] == "Too many requests"
    assert "Retry-After" in blocked.headers
    assert blocked.headers["X-RateLimit-Remaining"] == "0"


def test_validation_error_uses_standard_payload(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    path = f"/v1/t/{TENANT_ID}/valuations/snapshots/snap-1/results"
    response = client.post(path, json={}, headers=auth_headers)
    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Payload validation failed"
    assert isinstance(payload["detail"], list)
    assert response.headers["X-RateLimit-Limit"] == str(settings.rate_limit_requests)


def test_metrics_endpoint_exposes_custom_counters(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "safv_requests_total" in body or "requests_total" in body
    assert "rate_limit_hits_total" in body
