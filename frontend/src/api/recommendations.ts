import { apiFetch } from './http';
import type { CalculationJobStatus, RecommendationRunCreate, RecommendationRunResponse } from './types';

export async function createRecommendationRun(
  tenantId: string,
  token: string,
  payload: RecommendationRunCreate,
): Promise<CalculationJobStatus> {
  return apiFetch<CalculationJobStatus>(`/t/${encodeURIComponent(tenantId)}/recommendations/runs`, {
    method: 'POST',
    token,
    body: payload,
  });
}

export async function getRecommendationRun(
  tenantId: string,
  runId: string,
  token: string,
): Promise<RecommendationRunResponse> {
  return apiFetch<RecommendationRunResponse>(
    `/t/${encodeURIComponent(tenantId)}/recommendations/runs/${encodeURIComponent(runId)}`,
    {
      method: 'GET',
      token,
    },
  );
}
