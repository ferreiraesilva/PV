import { apiFetch } from './http';
import type {
  BenchmarkAggregationsResponse,
  BenchmarkIngestResponse,
} from './types';

export async function ingestBenchmarkDataset(
  tenantId: string,
  batchId: string,
  token: string,
  file: File
): Promise<BenchmarkIngestResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return apiFetch<BenchmarkIngestResponse>(
    `/t/${encodeURIComponent(tenantId)}/benchmarking/batches/${encodeURIComponent(batchId)}/ingest`,
    {
      method: 'POST',
      token,
      body: formData,
    }
  );
}

export async function listBenchmarkAggregations(
  tenantId: string,
  batchId: string,
  token: string
): Promise<BenchmarkAggregationsResponse> {
  return apiFetch<BenchmarkAggregationsResponse>(
    `/t/${encodeURIComponent(tenantId)}/benchmarking/batches/${encodeURIComponent(batchId)}/aggregations`,
    {
      method: 'GET',
      token,
    }
  );
}
