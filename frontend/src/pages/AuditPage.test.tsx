import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AuditPage from './AuditPage';
import * as AuthHook from '../hooks/useAuth';
import * as AuditAPI from '../api/audit';
import { AuditLogEntry, PaginatedAuditLogResponse } from '../api/types';

// Mock dependencies
vi.mock('../hooks/useAuth');
vi.mock('../api/audit');

const mockListAuditLogs = vi.spyOn(AuditAPI, 'listAuditLogs');

describe('AuditPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();

    // Mock useAuth to simulate an authenticated user
    vi.spyOn(AuthHook, 'useAuth').mockReturnValue({
      tenantId: 'test-tenant',
      accessToken: 'test-token',
      user: { email: 'test@example.com', roles: ['user'] },
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    });

    // Default mock for the API call
    mockListAuditLogs.mockResolvedValue({ logs: [], total: 0 });
  });

  it('should render the initial form elements', () => {
    render(<AuditPage />);
    expect(screen.getByText('Auditoria')).toBeInTheDocument();
    expect(screen.getByLabelText('De')).toBeInTheDocument();
    expect(screen.getByLabelText('Até')).toBeInTheDocument();
    expect(screen.getByLabelText('Request ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Usuário')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Buscar logs/i })
    ).toBeInTheDocument();
  });

  it('should fetch logs on initial render', () => {
    render(<AuditPage />);
    expect(mockListAuditLogs).toHaveBeenCalledTimes(1);
    expect(mockListAuditLogs).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      expect.objectContaining({
        skip: 0,
        limit: 20,
      })
    );
  });

  it('should call listAuditLogs with correct filters on form submission', async () => {
    render(<AuditPage />);

    // Fill out the form
    fireEvent.change(screen.getByLabelText('De'), {
      target: { value: '2024-01-01T10:00' },
    });
    fireEvent.change(screen.getByLabelText('Request ID'), {
      target: { value: 'req-123' },
    });

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Buscar logs/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockListAuditLogs).toHaveBeenCalledTimes(1);
    });

    // Check if the API was called with the correct arguments
    expect(mockListAuditLogs).toHaveBeenCalledWith(
      'test-tenant',
      'test-token',
      expect.objectContaining({
        from: new Date('2024-01-01T10:00').toISOString(),
        requestId: 'req-123',
        to: undefined,
        userId: undefined,
        skip: 0,
        limit: 20,
      })
    );
  });

  it('should clear filters when "Limpar filtros" is clicked', () => {
    render(<AuditPage />);
    const requestIdInput =
      screen.getByLabelText<HTMLInputElement>('Request ID');

    fireEvent.change(requestIdInput, { target: { value: 'test-id' } });
    expect(requestIdInput.value).toBe('test-id');

    const clearButton = screen.getByRole('button', { name: /Limpar filtros/i });
    fireEvent.click(clearButton);

    expect(requestIdInput.value).toBe('');
  });

  it('should display an error message when API call fails', async () => {
    mockListAuditLogs.mockRejectedValue(
      new Error('Falha na API de auditoria.')
    );
    render(<AuditPage />);

    const submitButton = screen.getByRole('button', { name: /Buscar logs/i });
    fireEvent.click(submitButton);

    expect(
      await screen.findByText('Falha na API de auditoria.')
    ).toBeInTheDocument();
  });

  it('should display "Consultando..." on the submit button when loading', () => {
    mockListAuditLogs.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<AuditPage />);

    const submitButton = screen.getByRole('button', { name: /Buscar logs/i });
    fireEvent.click(submitButton);

    expect(
      screen.getByRole('button', { name: /Consultando.../i })
    ).toBeInTheDocument();
  });

  it('should render the results table when logs are returned', async () => {
    const mockLogs: AuditLogEntry[] = [
      {
        id: 1,
        occurredAt: '2024-01-01T10:00:00Z',
        requestId: 'req-123',
        userId: 'user-456',
        method: 'POST',
        endpoint: '/v1/t/test-tenant/simulations/batches',
        statusCode: 200,
        tenantId: 'test-tenant',
      },
    ];
    mockListAuditLogs.mockResolvedValue({ logs: mockLogs, total: 1 });
    render(<AuditPage />);

    fireEvent.click(screen.getByRole('button', { name: /Buscar logs/i }));

    expect(await screen.findByText('req-123')).toBeInTheDocument();
    expect(screen.getByText('POST')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
  });

  it('should handle pagination', async () => {
    mockListAuditLogs.mockResolvedValue({ logs: [], total: 45 }); // 3 pages (20, 20, 5)
    render(<AuditPage />);

    // Wait for initial fetch
    await waitFor(() =>
      expect(screen.getByText('Página 1 de 3')).toBeInTheDocument()
    );

    const nextButton = screen.getByRole('button', { name: /Próxima/i });
    const prevButton = screen.getByRole('button', { name: /Anterior/i });

    expect(prevButton).toBeDisabled();
    expect(nextButton).not.toBeDisabled();

    // Go to next page
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(mockListAuditLogs).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(String),
        expect.objectContaining({ skip: 20, limit: 20 })
      );
    });
  });
});
