import { apiFetch } from './http';
import type { PaginatedAuditLogResponse } from './types';

interface AuditLogFilters {
  from?: string;
  to?: string;
  requestId?: string;
  userId?: string;
  limit?: number;
  after?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export async function listAuditLogs(
  tenantId: string,
  token: string,
  filters: AuditLogFilters
): Promise<PaginatedAuditLogResponse> {
  const query = new URLSearchParams(filters as Record<string, any>).toString();
  return apiFetch<PaginatedAuditLogResponse>(
    `/t/${tenantId}/admin/audit-logs?${query}`,
    {
      method: 'GET',
      token,
    }
  );
}
