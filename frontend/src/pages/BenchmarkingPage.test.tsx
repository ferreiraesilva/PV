import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import BenchmarkingPage from './BenchmarkingPage';
import * as AuthHook from '../hooks/useAuth';
import * as BenchmarkingHook from '../hooks/useBenchmarking';
import { BenchmarkAggregationItem } from '../api/types';

// Mock dependencies
vi.mock('../hooks/useAuth');
vi.mock('../hooks/useBenchmarking');

const mockUseBenchmarking = vi.spyOn(BenchmarkingHook, 'useBenchmarking');

describe('BenchmarkingPage', () => {
  // Mock das funções retornadas pelo hook useBenchmarking
  const mockActions = {
    setBatchId: vi.fn(),
    handleFileChange: vi.fn(),
    handleIngest: vi.fn(),
    fetchAggregations: vi.fn(),
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

    // Configuração padrão do mock do useBenchmarking
    mockUseBenchmarking.mockReturnValue({
      ...mockActions,
      batchId: '',
      aggregation: null,
      error: null,
      loading: false,
      fetching: false,
    });
  });

  it('should render the initial form elements', () => {
    render(<BenchmarkingPage />);
    expect(screen.getByText('Benchmarking de mercado')).toBeInTheDocument();
    expect(screen.getByLabelText('Batch ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Arquivo benchmarking')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Enviar dataset/i })
    ).toBeInTheDocument();
  });

  it('should call setBatchId when the batch ID input is changed', () => {
    render(<BenchmarkingPage />);
    const batchIdInput = screen.getByLabelText('Batch ID');
    fireEvent.change(batchIdInput, { target: { value: 'new-batch-id' } });
    expect(mockActions.setBatchId).toHaveBeenCalledWith('new-batch-id');
  });

  it('should call handleFileChange when a file is selected', () => {
    render(<BenchmarkingPage />);
    const fileInput = screen.getByLabelText('Arquivo benchmarking');
    const file = new File(['content'], 'test.csv', { type: 'text/csv' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    expect(mockActions.handleFileChange).toHaveBeenCalledTimes(1);
  });

  it('should call handleIngest when the form is submitted', () => {
    render(<BenchmarkingPage />);
    const submitButton = screen.getByRole('button', {
      name: /Enviar dataset/i,
    });
    fireEvent.click(submitButton);
    expect(mockActions.handleIngest).toHaveBeenCalledTimes(1);
  });

  it('should call fetchAggregations when the refresh button is clicked', () => {
    render(<BenchmarkingPage />);
    const refreshButton = screen.getByRole('button', {
      name: /Atualizar agregações/i,
    });
    fireEvent.click(refreshButton);
    expect(mockActions.fetchAggregations).toHaveBeenCalledTimes(1);
  });

  it('should display an error message when error state is set', () => {
    mockUseBenchmarking.mockReturnValue({
      ...mockActions,
      batchId: '',
      aggregation: null,
      error: 'Falha no processamento.',
      loading: false,
      fetching: false,
    });
    render(<BenchmarkingPage />);
    expect(screen.getByText('Falha no processamento.')).toBeInTheDocument();
  });

  it('should display "Processando..." on the submit button when loading', () => {
    mockUseBenchmarking.mockReturnValue({
      ...mockActions,
      batchId: '',
      aggregation: null,
      error: null,
      loading: true,
      fetching: false,
    });
    render(<BenchmarkingPage />);
    expect(
      screen.getByRole('button', { name: /Processando.../i })
    ).toBeInTheDocument();
  });

  it('should display "Buscando..." on the refresh button when fetching', () => {
    mockUseBenchmarking.mockReturnValue({
      ...mockActions,
      batchId: '',
      aggregation: null,
      error: null,
      loading: false,
      fetching: true,
    });
    render(<BenchmarkingPage />);
    expect(
      screen.getByRole('button', { name: /Buscando.../i })
    ).toBeInTheDocument();
  });

  it('should render the results table when aggregation state is set', () => {
    const mockAggregation: {
      batchId: string;
      rows: BenchmarkAggregationItem[];
      totalRows: number;
      discardedRows: number;
    } = {
      batchId: 'test-batch',
      totalRows: 100,
      discardedRows: 5,
      rows: [
        {
          metricCode: 'turnover',
          segmentBucket: 'SME',
          regionBucket: 'Southeast',
          count: 10,
          averageValue: 50000,
          minValue: 10000,
          maxValue: 90000,
        },
      ],
    };

    mockUseBenchmarking.mockReturnValue({
      ...mockActions,
      batchId: 'test-batch',
      aggregation: mockAggregation,
      error: null,
      loading: false,
      fetching: false,
    });

    render(<BenchmarkingPage />);
    expect(screen.getByText('Agregações do lote')).toBeInTheDocument();
    expect(screen.getByText('Linhas processadas')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('turnover')).toBeInTheDocument(); // Metric code in table
    expect(screen.getByText('SME')).toBeInTheDocument(); // Segment in table
  });
});
