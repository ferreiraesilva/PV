import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useRecommendations } from './useRecommendations';
import * as AuthHook from './useAuth';
import * as RecommendationsAPI from '../api/recommendations';

// Mock dependencies
vi.mock('./useAuth');
vi.mock('../api/recommendations');

const mockCreateRecommendationRun = vi.spyOn(
  RecommendationsAPI,
  'createRecommendationRun'
);
const mockGetRecommendationRun = vi.spyOn(
  RecommendationsAPI,
  'getRecommendationRun'
);

describe('useRecommendations', () => {
  const mockTenantId = 'test-tenant';
  const mockAccessToken = 'test-token';
  const mockEvent = { preventDefault: vi.fn() } as unknown as React.FormEvent;

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

    mockCreateRecommendationRun.mockResolvedValue({
      jobId: 'job-123',
      status: 'queued',
      submittedAt: new Date().toISOString(),
    });
    mockGetRecommendationRun.mockResolvedValue({
      runId: 'job-123',
      tenantId: mockTenantId,
      runType: 'pricing',
      status: 'completed',
      items: [],
      createdAt: new Date().toISOString(),
    });
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useRecommendations());

    expect(result.current.runType).toBe('pricing');
    expect(result.current.jobStatus).toBeNull();
    expect(result.current.runDetail).toBeNull();
    expect(result.current.error).toBeNull();
  });

  describe('handleStartRun', () => {
    it('should set an error for invalid JSON parameters', async () => {
      const { result } = renderHook(() => useRecommendations());

      act(() => {
        result.current.setParameters('{ "invalid-json" }');
      });

      await act(async () => {
        await result.current.handleStartRun(mockEvent);
      });

      expect(result.current.error).toBe('Parâmetros devem ser um JSON válido.');
      expect(mockCreateRecommendationRun).not.toHaveBeenCalled();
    });

    it('should call createRecommendationRun and update state on success', async () => {
      const { result } = renderHook(() => useRecommendations());

      await act(async () => {
        await result.current.handleStartRun(mockEvent);
      });

      expect(mockCreateRecommendationRun).toHaveBeenCalledTimes(1);
      expect(result.current.jobStatus?.jobId).toBe('job-123');
      expect(result.current.runId).toBe('job-123'); // Should be set for convenience
      expect(result.current.runDetail).toBeNull(); // Should clear previous details
      expect(result.current.error).toBeNull();
    });

    it('should handle API errors gracefully', async () => {
      mockCreateRecommendationRun.mockRejectedValue(new Error('API Error'));
      const { result } = renderHook(() => useRecommendations());

      await act(async () => {
        await result.current.handleStartRun(mockEvent);
      });

      expect(result.current.error).toBe('API Error');
      expect(result.current.jobStatus).toBeNull();
    });
  });

  describe('handleFetchRun', () => {
    it('should set an error if runId is missing', async () => {
      const { result } = renderHook(() => useRecommendations());

      await act(async () => {
        await result.current.handleFetchRun();
      });

      expect(result.current.error).toBe(
        'Informe o runId retornado pelo backend.'
      );
      expect(mockGetRecommendationRun).not.toHaveBeenCalled();
    });

    it('should call getRecommendationRun and update state on success', async () => {
      const { result } = renderHook(() => useRecommendations());

      act(() => {
        result.current.setRunId('job-123');
      });

      await act(async () => {
        await result.current.handleFetchRun();
      });

      expect(mockGetRecommendationRun).toHaveBeenCalledWith(
        mockTenantId,
        'job-123',
        mockAccessToken
      );
      expect(result.current.runDetail?.runId).toBe('job-123');
      expect(result.current.error).toBeNull();
    });

    it('should handle API errors gracefully', async () => {
      mockGetRecommendationRun.mockRejectedValue(new Error('Fetch Failed'));
      const { result } = renderHook(() => useRecommendations());

      act(() => {
        result.current.setRunId('job-123');
      });

      await act(async () => {
        await result.current.handleFetchRun();
      });

      expect(result.current.error).toBe('Fetch Failed');
      expect(result.current.runDetail).toBeNull();
    });
  });

  it('should manage loading and fetching states correctly', async () => {
    const { result } = renderHook(() => useRecommendations());

    const startPromise = act(async () => {
      await result.current.handleStartRun(mockEvent);
    });
    expect(result.current.loading).toBe(true);
    await startPromise;
    expect(result.current.loading).toBe(false);

    const fetchPromise = act(async () => {
      await result.current.handleFetchRun();
    });
    expect(result.current.fetching).toBe(true);
    await fetchPromise;
    expect(result.current.fetching).toBe(false);
  });
});
