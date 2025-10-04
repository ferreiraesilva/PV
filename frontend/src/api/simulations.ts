import { apiFetch } from './http';
import type { SimulationRequest, SimulationResponse } from './types';

export async function createSimulation(
  tenantId: string,
  token: string,
  payload: SimulationRequest,
): Promise<SimulationResponse> {
  return apiFetch<SimulationResponse>(`/t/${encodeURIComponent(tenantId)}/simulations`, {
    method: 'POST',
    token,
    body: payload,
  });
}
