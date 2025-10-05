import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import DashboardPage from './DashboardPage';
import * as AuthHook from '../hooks/useAuth';

// Mock dependencies
vi.mock('../hooks/useAuth');

const mockUseAuth = vi.spyOn(AuthHook, 'useAuth');

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('should render tenant context information', () => {
    const tenantId = 'test-tenant-123';
    mockUseAuth.mockReturnValue({
      tenantId,
      accessToken: 'token',
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    });

    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>,
    );

    expect(screen.getByText('Painel do SAFV')).toBeInTheDocument();
    expect(screen.getByText('Tenant ativo')).toBeInTheDocument();
    expect(screen.getByText(tenantId)).toBeInTheDocument();
  });

  it('should render all action cards with correct links', () => {
    mockUseAuth.mockReturnValue({ tenantId: 'test-tenant', accessToken: 'token', user: null, login: vi.fn(), logout: vi.fn(), refresh: vi.fn() });

    render(<BrowserRouter><DashboardPage /></BrowserRouter>);

    expect(screen.getByText('Simulações financeiras')).toBeInTheDocument();
    expect(screen.getByText('Valuation de carteira')).toBeInTheDocument();
    expect(screen.getByText('Benchmarking')).toBeInTheDocument();

    const links = screen.getAllByRole('link', { name: /Abrir módulo/i });
    expect(links).toHaveLength(5);
    expect(links[0]).toHaveAttribute('href', '/simulations');
    expect(links[1]).toHaveAttribute('href', '/valuations');
    expect(links[2]).toHaveAttribute('href', '/benchmarking');
  });
});