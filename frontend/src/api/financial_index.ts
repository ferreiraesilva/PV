import { apiFetch } from './http';
import type { IndexValueBatchInput, IndexValueOutput } from './types';

export async function listIndexValues(
  tenantId: string,
  token: string,
  indexCode: string,
): Promise<IndexValueOutput[]> {
  return apiFetch<IndexValueOutput[]>(`/t/${tenantId}/indexes/${indexCode}/values`, {
    method: 'GET',
    token,
  });
}

export async function createIndexValues(
  tenantId: string,
  token: string,
  indexCode: string,
  payload: IndexValueBatchInput,
): Promise<IndexValueOutput[]> {
  return apiFetch<IndexValueOutput[]>(`/t/${tenantId}/indexes/${indexCode}/values`, {
    method: 'POST',
    token,
    body: payload,
  });
}