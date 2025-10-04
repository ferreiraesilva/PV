import { apiFetch } from './http';
import type { AuditLogEntry } from './types';

export interface AuditFilters {
  from?: string;
  to?: string;
  requestId?: string;
  userId?: string;
}

export async function listAuditLogs(
  tenantId: string,
  token: string,
  filters: AuditFilters = {},
): Promise<AuditLogEntry[]> {
  const params = new URLSearchParams();
  if (filters.from) params.set('from', filters.from);
  if (filters.to) params.set('to', filters.to);
  if (filters.requestId) params.set('requestId', filters.requestId);
  if (filters.userId) params.set('userId', filters.userId);

  const query = params.toString();
  const url = `/t/${encodeURIComponent(tenantId)}/audit/logs${query ? `?${query}` : ''}`;
  return apiFetch<AuditLogEntry[]>(url, {
    method: 'GET',
    token,
  });
}
