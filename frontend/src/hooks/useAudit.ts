import { FormEvent, useState, useEffect, useCallback } from 'react';

import { listAuditLogs } from '../api/audit';
import type { AuditLogEntry } from '../api/types';
import { useAuth } from './useAuth';

interface AuditFiltersState {
  from: string;
  to: string;
  requestId: string;
  userId: string;
}

const DEFAULT_FILTERS: AuditFiltersState = {
  from: '',
  to: '',
  requestId: '',
  userId: '',
};

const LIMIT = 20;

export const useAudit = () => {
  const { tenantId, accessToken } = useAuth();
  const [filters, setFilters] = useState<AuditFiltersState>(DEFAULT_FILTERS);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageCursors, setPageCursors] = useState<Array<string | undefined>>([undefined]);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [sortBy, setSortBy] = useState<keyof AuditLogEntry>('occurredAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const fetchLogs = useCallback(
    async (cursor: string | undefined, currentFilters: AuditFiltersState) => {
    if (!tenantId || !accessToken) return;

    setError(null);
    try {
      setLoading(true);
      const cleanFilters = {
        from: currentFilters.from ? new Date(currentFilters.from).toISOString() : undefined,
        to: currentFilters.to ? new Date(currentFilters.to).toISOString() : undefined,
        requestId: currentFilters.requestId || undefined,
        userId: currentFilters.userId || undefined,
        limit: LIMIT,
        after: cursor,
        sortBy: sortBy,
        sortOrder: sortOrder,
      };
      const response = await listAuditLogs(tenantId, accessToken, cleanFilters);
      setLogs(response.items);
      setHasNextPage(response.hasNextPage);
      if (response.hasNextPage && response.nextCursor) {
        setPageCursors(current => {
          const next = [...current];
          next[page] = response.nextCursor;
          return next.slice(0, page + 1);
        });
      }
    } catch (err) {
      const message = (err as Error).message ?? 'Erro ao consultar auditoria.';
      setError(message);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [accessToken, tenantId, sortBy, sortOrder]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setPage(1);
    setPageCursors([undefined]);
    fetchLogs(undefined, filters);
  };

  const handleClear = () => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
    setPageCursors([undefined]);
    fetchLogs(undefined, DEFAULT_FILTERS);
  };

  const handleFilterChange = (field: keyof AuditFiltersState, value: string) => {
    setFilters(current => ({ ...current, [field]: value }));
  };

  const handleSort = (column: keyof AuditLogEntry) => {
    const newSortOrder = sortBy === column && sortOrder === 'desc' ? 'asc' : 'desc';
    setSortBy(column);
    setSortOrder(newSortOrder);
    // Reset pagination when sort order changes
    setPage(1);
    setPageCursors([undefined]);
  };

  useEffect(() => {
    fetchLogs(pageCursors[page - 1], filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sortBy, sortOrder]);

  return {
    filters, logs, error, loading, page, hasNextPage, sortBy, sortOrder,
    handleFilterChange, setPage, handleSubmit, handleClear, handleSort,
  };
};