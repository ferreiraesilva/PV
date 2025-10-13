import { apiFetch } from './http';
import type { SimulationBatchRequest, SimulationBatchResponse } from './types';

export async function createSimulation(
  tenantId: string,
  token: string,
  payload: SimulationBatchRequest
): Promise<SimulationBatchResponse> {
  return apiFetch<SimulationBatchResponse>(
    `/t/${encodeURIComponent(tenantId)}/simulations/batches`,
    {
      method: 'POST',
      token,
      body: payload,
    }
  );
}
