import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useValuations } from './useValuations';
import * as AuthHook from './useAuth';
import * as ValuationsAPI from '../api/valuations';

// Mock dependencies
vi.mock('./useAuth');
vi.mock('../api/valuations');

describe('useValuations', () => {
  const mockTenantId = 'test-tenant';
  const mockAccessToken = 'test-token';
  const mockEvent = { preventDefault: vi.fn() } as unknown as React.FormEvent;

  beforeEach(() => {
    // Reset mocks before each test
    vi.resetAllMocks();

    // Mock useAuth to simulate an authenticated user
    vi.spyOn(AuthHook, 'useAuth').mockReturnValue({
      tenantId: mockTenantId,
      accessToken: mockAccessToken,
      user: { email: 'test@example.com', roles: ['user'] },
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    });

    // Mock the valuation API
    vi.spyOn(ValuationsAPI, 'evaluateValuation').mockResolvedValue({
      tenant_id: mockTenantId,
      results: [{ code: 'base', gross_present_value: 1000, net_present_value: 950, expected_losses: 50 }],
    });
  });

  it('should initialize with default cashflows and scenarios', () => {
    const { result } = renderHook(() => useValuations());

    expect(result.current.cashflows.length).toBe(2);
    expect(result.current.scenarios.length).toBe(3);
    expect(result.current.snapshotId).toBe('');
    expect(result.current.error).toBeNull();
    expect(result.current.result).toBeNull();
  });

  it('should update a cashflow item', () => {
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.updateCashflow(0, 'amount', 20000);
    });

    expect(result.current.cashflows[0].amount).toBe(20000);
  });

  it('should add and remove a cashflow item', () => {
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.addCashflow();
    });
    expect(result.current.cashflows.length).toBe(3);

    act(() => {
      result.current.removeCashflow(2);
    });
    expect(result.current.cashflows.length).toBe(2);
  });

  it('should not submit if snapshotId is missing', async () => {
    const { result } = renderHook(() => useValuations());

    await act(async () => {
      await result.current.handleSubmit(mockEvent);
    });

    expect(result.current.error).toBe('Informe o snapshotId que será usado como referência.');
    expect(ValuationsAPI.evaluateValuation).not.toHaveBeenCalled();
  });

  it('should not submit if there are duplicate scenario codes', async () => {
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.setSnapshotId('snap-123');
      // Default scenarios: 'optimista', 'base', 'conservador'
      // Change 'base' to 'optimista' to create a duplicate
      result.current.updateScenario(1, 'code', 'optimista');
    });

    await act(async () => {
      await result.current.handleSubmit(mockEvent);
    });

    expect(result.current.error).toBe('Não são permitidos cenários com códigos duplicados. Por favor, ajuste os códigos e tente novamente.');
    expect(ValuationsAPI.evaluateValuation).not.toHaveBeenCalled();
  });

  it('should allow submission if duplicate codes are empty strings', async () => {
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.setSnapshotId('snap-123');
      result.current.updateScenario(0, 'code', '');
      result.current.updateScenario(1, 'code', '');
    });

    await act(async () => {
      await result.current.handleSubmit(mockEvent);
    });

    expect(result.current.error).toBeNull();
    expect(ValuationsAPI.evaluateValuation).toHaveBeenCalledTimes(1);
  });

  it('should handle successful submission', async () => {
    const evaluateValuationSpy = vi.spyOn(ValuationsAPI, 'evaluateValuation');
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.setSnapshotId('snap-123');
    });

    await act(async () => {
      await result.current.handleSubmit(mockEvent);
    });

    expect(result.current.submitting).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.result).not.toBeNull();
    expect(result.current.result?.results[0].code).toBe('base');

    expect(evaluateValuationSpy).toHaveBeenCalledTimes(1);
    expect(evaluateValuationSpy).toHaveBeenCalledWith(mockTenantId, mockAccessToken, {
      cashflows: expect.any(Array),
      scenarios: expect.any(Array),
    });
  });

  it('should handle API error on submission', async () => {
    const errorMessage = 'API Failure';
    const evaluateValuationSpy = vi.spyOn(ValuationsAPI, 'evaluateValuation').mockRejectedValue(new Error(errorMessage));
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.setSnapshotId('snap-123');
    });

    await act(async () => {
      await result.current.handleSubmit(mockEvent);
    });

    expect(result.current.submitting).toBe(false);
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBe(errorMessage);
    expect(evaluateValuationSpy).toHaveBeenCalledTimes(1);
  });

  it('should set submitting state during API call', async () => {
    const { result } = renderHook(() => useValuations());

    act(() => {
      result.current.setSnapshotId('snap-123');
    });

    // Don't await the call to check the intermediate state
    const promise = act(async () => {
      await result.current.handleSubmit(mockEvent);
    });

    expect(result.current.submitting).toBe(true);

    await promise;

    expect(result.current.submitting).toBe(false);
  });
});