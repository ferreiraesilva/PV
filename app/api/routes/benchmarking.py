from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, status, UploadFile

from app.api.deps import CurrentUser, require_roles
from app.api.schemas.benchmarking import (
    BenchmarkAggregationsResponse,
    BenchmarkIngestResponse,
)
from app.db.session import get_db
from app.services.benchmarking import AggregatedBenchmark, BenchmarkingService

router = APIRouter(tags=["Benchmarking"], prefix="/t/{tenant_id}/benchmarking")

service = BenchmarkingService()


def _parse_uuid(raw: str, *, field_name: str) -> UUID:
    try:
        return UUID(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field_name}"
        ) from exc


def _set_audit_context(
    request: Request,
    *,
    tenant_id: str,
    batch_id: str,
    aggregations: list[AggregatedBenchmark],
    current_user: CurrentUser,
) -> None:
    request.state.audit_actor_roles = current_user.roles
    request.state.audit_actor_user_id = current_user.user_id
    request.state.audit_resource_type = "benchmark_batch"
    request.state.audit_resource_id = batch_id
    payload = {
        "aggregations": [
            {
                "metric_code": item.metric_code,
                "segment_bucket": item.segment_bucket,
                "region_bucket": item.region_bucket,
                "count": item.count,
                "average_value": item.average_value,
                "min_value": item.min_value,
                "max_value": item.max_value,
            }
            for item in aggregations
        ]
    }
    request.state.audit_payload_out = payload
    request.state.audit_diffs = payload


def _to_response_items(
    aggregations: list[AggregatedBenchmark],
) -> list[dict[str, object]]:
    return [
        {
            "metricCode": item.metric_code,
            "segmentBucket": item.segment_bucket,
            "regionBucket": item.region_bucket,
            "count": item.count,
            "averageValue": item.average_value,
            "minValue": item.min_value,
            "maxValue": item.max_value,
        }
        for item in aggregations
    ]


@router.post("/batches/{batch_id}/ingest", response_model=BenchmarkIngestResponse)
async def ingest_benchmark_dataset(
    tenant_id: str,
    batch_id: str,
    request: Request,
    file: UploadFile | None = File(None),
    current_user: CurrentUser = Depends(require_roles("user", "superuser")),
    db=Depends(get_db),  # noqa: ARG001 - future persistence
) -> BenchmarkIngestResponse:
    tenant_uuid = _parse_uuid(tenant_id, field_name="tenant_id")
    batch_uuid = _parse_uuid(batch_id, field_name="batch_id")
    filename_override: Optional[str] = request.query_params.get("filename")

    if file is not None:
        content = await file.read()
        filename = file.filename or filename_override or "dataset.bin"
    else:
        content = await request.body()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File content required"
            )
        filename = filename_override or "dataset.bin"

    try:
        result = service.ingest_dataset(
            tenant_uuid,
            batch_uuid,
            filename=filename,
            content=content,
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    _set_audit_context(
        request,
        tenant_id=tenant_id,
        batch_id=batch_id,
        aggregations=result.aggregations,
        current_user=current_user,
    )

    return BenchmarkIngestResponse(
        tenantId=result.tenant_id,
        batchId=result.batch_id,
        totalRows=result.total_rows,
        discardedRows=result.discarded_rows,
        aggregations=_to_response_items(result.aggregations),
    )


@router.get(
    "/batches/{batch_id}/aggregations", response_model=BenchmarkAggregationsResponse
)
def list_benchmark_aggregations(
    tenant_id: str,
    batch_id: str,
    request: Request,
    current_user: CurrentUser = Depends(require_roles("user", "superuser")),
    db=Depends(get_db),  # noqa: ARG001 - future persistence
) -> BenchmarkAggregationsResponse:
    tenant_uuid = _parse_uuid(tenant_id, field_name="tenant_id")
    batch_uuid = _parse_uuid(batch_id, field_name="batch_id")

    aggregations = service.list_aggregations(tenant_uuid, batch_uuid)

    _set_audit_context(
        request,
        tenant_id=tenant_id,
        batch_id=batch_id,
        aggregations=aggregations,
        current_user=current_user,
    )

    return BenchmarkAggregationsResponse(
        tenantId=tenant_uuid,
        batchId=batch_uuid,
        aggregations=_to_response_items(aggregations),
    )
