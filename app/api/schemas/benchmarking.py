from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AggregatedBenchmarkResponse(BaseModel):
    metric_code: str = Field(..., alias="metricCode")
    segment_bucket: str = Field(..., alias="segmentBucket")
    region_bucket: str = Field(..., alias="regionBucket")
    count: int
    average_value: float = Field(..., alias="averageValue")
    min_value: float = Field(..., alias="minValue")
    max_value: float = Field(..., alias="maxValue")

    model_config = ConfigDict(populate_by_name=True)


class BenchmarkIngestResponse(BaseModel):
    tenant_id: UUID = Field(..., alias="tenantId")
    batch_id: UUID = Field(..., alias="batchId")
    total_rows: int = Field(..., alias="totalRows")
    discarded_rows: int = Field(..., alias="discardedRows")
    aggregations: list[AggregatedBenchmarkResponse]

    model_config = ConfigDict(populate_by_name=True)


class BenchmarkAggregationsResponse(BaseModel):
    tenant_id: UUID = Field(..., alias="tenantId")
    batch_id: UUID = Field(..., alias="batchId")
    aggregations: list[AggregatedBenchmarkResponse]

    model_config = ConfigDict(populate_by_name=True)