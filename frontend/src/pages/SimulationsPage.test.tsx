import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import SimulationsPage from './SimulationsPage';
import * as AuthHook from '../hooks/useAuth';
import * as SimulationsHook from '../hooks/useSimulations';
import { PlanFormState } from '../hooks/usePlansState';

// Mock dependencies
vi.mock('../hooks/useAuth');
vi.mock('../hooks/useSimulations');

const mockUseSimulations = vi.spyOn(SimulationsHook, 'useSimulations');

// Helper para criar um plano mock
const createMockPlan = (index: number): PlanFormState => ({
  key: `plan-key-${index}`,
  label: `Plano ${index + 1}`,
  productCode: '',
  principal: 3000,
  discountRate: 1.5,
  discountRatePeriod: 'monthly',
  baseDate: '2024-01-01',
  adjustmentIndex: 'INCC',
  adjustmentPeriodicity: 'monthly',
  adjustmentAddonRate: 1,
  installments: [{ due_date: '2024-02-01', amount: 3000 }],
});

describe('SimulationsPage', () => {
  // Mock das funções retornadas pelo hook useSimulations
  const mockActions = {
    updatePlanField: vi.fn(),
    updateInstallment: vi.fn(),
    addInstallment: vi.fn(),
    removeInstallment: vi.fn(),
    addPlan: vi.fn(),
    removePlan: vi.fn(),
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

    // Configuração padrão do mock do useSimulations
    mockUseSimulations.mockReturnValue({
      ...mockActions,
      plans: [createMockPlan(0)],
      result: null,
      error: null,
      submitting: false,
      canRemovePlan: false,
    });
  });

  it('should render the initial plan and form elements', () => {
    render(<SimulationsPage />);
    expect(screen.getByText('Plano 1')).toBeInTheDocument();
    expect(screen.getByLabelText('Nome do plano')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Calcular comparativo/i })).toBeInTheDocument();
  });

  it('should call addPlan when "Adicionar plano" is clicked', () => {
    render(<SimulationsPage />);
    const addButton = screen.getByRole('button', { name: /Adicionar plano/i });
    fireEvent.click(addButton);
    expect(mockActions.addPlan).toHaveBeenCalledTimes(1);
  });

  it('should call updatePlanField when a plan input is changed', () => {
    render(<SimulationsPage />);
    const labelInput = screen.getByLabelText('Nome do plano');
    fireEvent.change(labelInput, { target: { value: 'New Plan Name' } });
    expect(mockActions.updatePlanField).toHaveBeenCalledWith(0, 'label', 'New Plan Name');
  });

  it('should call handleSubmit when the form is submitted', () => {
    render(<SimulationsPage />);
    const submitButton = screen.getByRole('button', { name: /Calcular comparativo/i });
    fireEvent.click(submitButton);
    expect(mockActions.handleSubmit).toHaveBeenCalledTimes(1);
  });

  it('should disable the "Remover plano" button when there is only one plan', () => {
    render(<SimulationsPage />);
    const removeButton = screen.getByRole('button', { name: /Remover plano/i });
    expect(removeButton).toBeDisabled();
  });

  it('should enable the "Remover plano" button when there are multiple plans', () => {
    // Sobrescreve o mock para este teste específico
    mockUseSimulations.mockReturnValue({
      ...mockActions,
      plans: [createMockPlan(0), createMockPlan(1)],
      result: null,
      error: null,
      submitting: false,
      canRemovePlan: true,
    });

    render(<SimulationsPage />);
    const removeButtons = screen.getAllByRole('button', { name: /Remover plano/i });
    expect(removeButtons[0]).not.toBeDisabled();
    expect(removeButtons[1]).not.toBeDisabled();
  });

  it('should display an error message when error state is set', () => {
    mockUseSimulations.mockReturnValue({
      ...mockActions,
      plans: [createMockPlan(0)],
      result: null,
      error: 'Ocorreu um erro na simulação.',
      submitting: false,
      canRemovePlan: false,
    });

    render(<SimulationsPage />);
    expect(screen.getByText('Ocorreu um erro na simulação.')).toBeInTheDocument();
  });

  it('should display "Calculando..." on the submit button when submitting', () => {
    mockUseSimulations.mockReturnValue({
      ...mockActions,
      plans: [createMockPlan(0)],
      result: null,
      error: null,
      submitting: true,
      canRemovePlan: false,
    });

    render(<SimulationsPage />);
    expect(screen.getByRole('button', { name: /Calculando.../i })).toBeInTheDocument();
  });
});