import { apiFetch } from './http';
import type { ValuationRequest, ValuationResponse } from './types';

export async function evaluateValuation(
  tenantId: string,
  snapshotId: string,
  token: string,
  payload: ValuationRequest
): Promise<ValuationResponse> {
  return apiFetch<ValuationResponse>(
    `/t/${encodeURIComponent(tenantId)}/valuations/snapshots/${encodeURIComponent(snapshotId)}/results`,
    {
      method: 'POST',
      token,
      body: payload,
    }
  );
}
