import { apiFetch } from './http';
import type { BenchmarkAggregationsResponse, BenchmarkIngestResponse } from './types';

export async function ingestBenchmarkDataset(
  tenantId: string,
  batchId: string,
  token: string,
  file: File,
): Promise<BenchmarkIngestResponse> {
  const filename = file.name || 'dataset.csv';
  return apiFetch<BenchmarkIngestResponse>(
    `/t/${encodeURIComponent(tenantId)}/benchmarking/batches/${encodeURIComponent(batchId)}/ingest?filename=${encodeURIComponent(filename)}`,
    {
      method: 'POST',
      token,
      headers: { 'Content-Type': file.type || 'application/octet-stream' },
      body: file,
    },
  );
}

export async function listBenchmarkAggregations(
  tenantId: string,
  batchId: string,
  token: string,
): Promise<BenchmarkAggregationsResponse> {
  return apiFetch<BenchmarkAggregationsResponse>(
    `/t/${encodeURIComponent(tenantId)}/benchmarking/batches/${encodeURIComponent(batchId)}/aggregations`,
    {
      method: 'GET',
      token,
    },
  );
}
