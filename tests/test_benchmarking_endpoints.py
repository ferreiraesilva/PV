from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from tests.conftest import TENANT_ID


def _headers_with_auth(base_headers: dict[str, str]) -> dict[str, str]:
    merged = base_headers.copy()
    merged.setdefault("Content-Type", "application/octet-stream")
    return merged


def test_benchmark_ingest_csv_returns_aggregations(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    batch_id = uuid4()
    csv_content = """metric_code,segment,region,value
default_rate,PME Financas,Sudeste,1.2
DEFAULT_RATE,PME Financas,Sudeste,1.4
default_rate,PME Financas,Sudeste,1.0
default_rate,PME Financas,Sul,1.6
default_rate,,Sudeste,1.1
""".encode(
        "utf-8"
    )
    response = client.post(
        f"/v1/t/{TENANT_ID}/benchmarking/batches/{batch_id}/ingest",
        params={"filename": "dataset.csv"},
        headers=_headers_with_auth(auth_headers),
        content=csv_content,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["totalRows"] == 5
    assert payload["discardedRows"] == 1
    assert payload["tenantId"] == TENANT_ID
    assert payload["batchId"] == str(batch_id)
    assert len(payload["aggregations"]) == 1
    aggregation = payload["aggregations"][0]
    assert aggregation["segmentBucket"].endswith("*")
    assert aggregation["regionBucket"].endswith("*")
    assert aggregation["count"] == 4
    assert aggregation["metricCode"] == "DEFAULT_RATE"


def test_benchmark_ingest_discards_low_cardinality_groups(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    batch_id = uuid4()
    csv_content = """metric_code,segment,region,value
spread,Enterprise Servicos,Sul,2
spread,Enterprise Servicos,Sudeste,3
spread,Enterprise Servicos,Norte,4
spread,Enterprise Servicos,Sul,2.5
vpl,Micro Comercio,Sudeste,1.0
vpl,Micro Comercio,Sudeste,1.1
""".encode(
        "utf-8"
    )
    response = client.post(
        f"/v1/t/{TENANT_ID}/benchmarking/batches/{batch_id}/ingest",
        params={"filename": "metrics.csv"},
        headers=_headers_with_auth(auth_headers),
        content=csv_content,
    )
    assert response.status_code == 200
    data = response.json()
    buckets = {item["metricCode"] for item in data["aggregations"]}
    assert "SPREAD" in buckets
    assert "VPL" not in buckets  # only two rows -> should be dropped


def test_benchmark_get_aggregations_returns_latest_data(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    batch_id = uuid4()
    csv_content = """metric_code,segment,region,value
inadimplencia,Large Industrias,Sudeste,5
inadimplencia,Large Industrias,Sudeste,4.5
inadimplencia,Large Industrias,Sudeste,5.5
""".encode(
        "utf-8"
    )
    ingest_response = client.post(
        f"/v1/t/{TENANT_ID}/benchmarking/batches/{batch_id}/ingest",
        params={"filename": "data.csv"},
        headers=_headers_with_auth(auth_headers),
        content=csv_content,
    )
    assert ingest_response.status_code == 200

    response = client.get(
        f"/v1/t/{TENANT_ID}/benchmarking/batches/{batch_id}/aggregations",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tenantId"] == TENANT_ID
    assert data["batchId"] == str(batch_id)
    assert len(data["aggregations"]) == 1
    aggregation = data["aggregations"][0]
    assert aggregation["metricCode"] == "INADIMPLENCIA"
    assert aggregation["count"] == 3
