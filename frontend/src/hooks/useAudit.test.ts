import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useAudit } from './useAudit';
import * as AuthHook from './useAuth';
import * as AuditAPI from '../api/audit';

// Mock dependencies
vi.mock('./useAuth');
vi.mock('../api/audit');

const mockListAuditLogs = vi.spyOn(AuditAPI, 'listAuditLogs');

describe('useAudit', () => {
  const mockTenantId = 'test-tenant';
  const mockAccessToken = 'test-token';

  beforeEach(() => {
    vi.resetAllMocks();

    vi.spyOn(AuthHook, 'useAuth').mockReturnValue({
      tenantId: mockTenantId,
      accessToken: mockAccessToken,
      user: { email: 'test@example.com', roles: ['user'] },
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    });

    mockListAuditLogs.mockResolvedValue({ items: [], hasNextPage: false });
  });

  it('should initialize with default sorting state', () => {
    renderHook(() => useAudit());

    // The useEffect triggers an initial fetch
    expect(mockListAuditLogs).toHaveBeenCalledWith(
      mockTenantId,
      mockAccessToken,
      expect.objectContaining({
        sortBy: 'occurredAt',
        sortOrder: 'desc',
      }),
    );
  });

  it('should toggle sort order when sorting by the same column', async () => {
    const { result } = renderHook(() => useAudit());

    // Initial state is occurredAt, desc. First click should change to asc.
    act(() => {
      result.current.handleSort('occurredAt');
    });

    await waitFor(() => {
      expect(result.current.sortBy).toBe('occurredAt');
      expect(result.current.sortOrder).toBe('asc');
    });

    // Second click should change back to desc.
    act(() => {
      result.current.handleSort('occurredAt');
    });

    await waitFor(() => {
      expect(result.current.sortBy).toBe('occurredAt');
      expect(result.current.sortOrder).toBe('desc');
    });
  });

  it('should change sort column and reset order to desc', async () => {
    const { result } = renderHook(() => useAudit());

    // Change from default 'occurredAt' to 'statusCode'
    act(() => {
      result.current.handleSort('statusCode');
    });

    await waitFor(() => {
      expect(result.current.sortBy).toBe('statusCode');
      expect(result.current.sortOrder).toBe('desc');
    });
  });

  it('should reset pagination when sorting changes', async () => {
    const { result } = renderHook(() => useAudit());

    // Go to page 2
    act(() => {
      result.current.setPage(2);
    });

    // Change sort
    act(() => {
      result.current.handleSort('method');
    });

    await waitFor(() => {
      // Page should be reset to 1
      expect(result.current.page).toBe(1);
    });
  });

  it('should trigger a new data fetch with correct sort parameters', async () => {
    const { result } = renderHook(() => useAudit());

    // Wait for initial fetch to complete
    await waitFor(() => expect(mockListAuditLogs).toHaveBeenCalledTimes(1));

    act(() => {
      result.current.handleSort('endpoint');
    });

    await waitFor(() => {
      // A second fetch should have been triggered by the useEffect
      expect(mockListAuditLogs).toHaveBeenCalledTimes(2);
      expect(mockListAuditLogs).toHaveBeenLastCalledWith(
        mockTenantId,
        mockAccessToken,
        expect.objectContaining({
          sortBy: 'endpoint',
          sortOrder: 'desc',
        }),
      );
    });
  });
});