import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ValuationsPage from './ValuationsPage';
import * as AuthHook from '../hooks/useAuth';
import * as ValuationsHook from '../hooks/useValuations';
import {
  ValuationCashflowInput,
  ValuationResponse,
  ValuationScenarioInput,
} from '../api/types';

// Mock dependencies
vi.mock('../hooks/useAuth');
vi.mock('../hooks/useValuations');

const mockUseValuations = vi.spyOn(ValuationsHook, 'useValuations');

// Helper to create mock data
const createMockCashflow = (index: number): ValuationCashflowInput => ({
  due_date: '2024-01-01',
  amount: 1000 * (index + 1),
  probability_default: 0.05,
  probability_cancellation: 0.02,
});

const createMockScenario = (index: number): ValuationScenarioInput => ({
  code: `cenario-${index}`,
  discount_rate: 0.015,
  default_multiplier: 1,
  cancellation_multiplier: 1,
});

describe('ValuationsPage', () => {
  // Mock das funções retornadas pelo hook useValuations
  const mockActions = {
    setSnapshotId: vi.fn(),
    updateCashflow: vi.fn(),
    addCashflow: vi.fn(),
    removeCashflow: vi.fn(),
    updateScenario: vi.fn(),
    addScenario: vi.fn(),
    removeScenario: vi.fn(),
    handleSubmit: vi.fn(),
  };

  beforeEach(() => {
    vi.resetAllMocks();

    // Mock do useAuth
    vi.spyOn(AuthHook, 'useAuth').mockReturnValue({
      tenantId: 'test-tenant',
      accessToken: 'test-token',
      user: { email: 'test@example.com', roles: ['user'] },
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
    });

    // Configuração padrão do mock do useValuations
    mockUseValuations.mockReturnValue({
      ...mockActions,
      snapshotId: '',
      cashflows: [createMockCashflow(0)],
      scenarios: [createMockScenario(0)],
      result: null,
      error: null,
      submitting: false,
    });
  });

  it('should render the initial form elements', () => {
    render(<ValuationsPage />);
    expect(screen.getByText('Fluxos de caixa')).toBeInTheDocument();
    expect(screen.getByText('Cenários')).toBeInTheDocument();
    expect(screen.getByLabelText('Snapshot ID')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Executar cenários/i })
    ).toBeInTheDocument();
  });

  it('should call addCashflow when "Adicionar fluxo" is clicked', () => {
    render(<ValuationsPage />);
    const addButton = screen.getByRole('button', { name: /Adicionar fluxo/i });
    fireEvent.click(addButton);
    expect(mockActions.addCashflow).toHaveBeenCalledTimes(1);
  });

  it('should call updateScenario when a scenario input is changed', () => {
    render(<ValuationsPage />);
    const codeInput = screen.getByDisplayValue('cenario-0');
    fireEvent.change(codeInput, { target: { value: 'novo-codigo' } });
    expect(mockActions.updateScenario).toHaveBeenCalledWith(
      0,
      'code',
      'novo-codigo'
    );
  });

  it('should call handleSubmit when the form is submitted', () => {
    render(<ValuationsPage />);
    const submitButton = screen.getByRole('button', {
      name: /Executar cenários/i,
    });
    fireEvent.click(submitButton);
    expect(mockActions.handleSubmit).toHaveBeenCalledTimes(1);
  });

  it('should disable remove buttons when there is only one item', () => {
    render(<ValuationsPage />);
    // Os botões de remover são identificados pelo seu conteúdo textual '×'
    const removeButtons = screen.getAllByRole('button', { name: '✕' });
    expect(removeButtons[0]).toBeDisabled(); // Cashflow remove button
    expect(removeButtons[1]).toBeDisabled(); // Scenario remove button
  });

  it('should display an error message when error state is set', () => {
    mockUseValuations.mockReturnValue({
      ...mockActions,
      snapshotId: '',
      cashflows: [createMockCashflow(0)],
      scenarios: [createMockScenario(0)],
      result: null,
      error: 'Falha na avaliação.',
      submitting: false,
    });

    render(<ValuationsPage />);
    expect(screen.getByText('Falha na avaliação.')).toBeInTheDocument();
  });

  it('should display "Executando..." on the submit button when submitting', () => {
    mockUseValuations.mockReturnValue({
      ...mockActions,
      snapshotId: '',
      cashflows: [createMockCashflow(0)],
      scenarios: [createMockScenario(0)],
      result: null,
      error: null,
      submitting: true,
    });

    render(<ValuationsPage />);
    expect(
      screen.getByRole('button', { name: /Executando.../i })
    ).toBeInTheDocument();
  });

  it('should render the results table when result state is set', () => {
    const mockResult: ValuationResponse = {
      tenant_id: 'test-tenant',
      results: [
        {
          code: 'base',
          gross_present_value: 1000,
          net_present_value: 950,
          expected_losses: 50,
        },
      ],
    };
    mockUseValuations.mockReturnValue({
      ...mockActions,
      snapshotId: '',
      cashflows: [],
      scenarios: [],
      result: mockResult,
      error: null,
      submitting: false,
    });

    render(<ValuationsPage />);
    expect(screen.getByText('Resultados consolidados')).toBeInTheDocument();
    expect(screen.getByText('base')).toBeInTheDocument(); // Scenario code in table
    expect(screen.getByText('R$ 1.000,00')).toBeInTheDocument(); // Gross PV
  });
});
