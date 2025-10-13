import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import RecommendationsPage from './RecommendationsPage';
import * as AuthHook from '../hooks/useAuth';
import * as RecommendationsAPI from '../api/recommendations';
import { CalculationJobStatus, RecommendationRunResponse } from '../api/types';

// Mock dependencies
vi.mock('../hooks/useAuth');
vi.mock('../api/recommendations');

const mockCreateRecommendationRun = vi.spyOn(
  RecommendationsAPI,
  'createRecommendationRun'
);
const mockGetRecommendationRun = vi.spyOn(
  RecommendationsAPI,
  'getRecommendationRun'
);

describe('RecommendationsPage', () => {
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

    // Default mocks for the API calls
    const mockJobStatus: CalculationJobStatus = {
      jobId: 'job-123',
      status: 'queued',
      submittedAt: new Date().toISOString(),
    };
    mockCreateRecommendationRun.mockResolvedValue(mockJobStatus);

    const mockRunResponse: RecommendationRunResponse = {
      runId: 'job-123',
      tenantId: 'test-tenant',
      runType: 'pricing',
      status: 'completed',
      items: [
        {
          title: 'Recommendation 1',
          description: 'Details here',
          priority: 'high',
        },
      ],
      createdAt: new Date().toISOString(),
    };
    mockGetRecommendationRun.mockResolvedValue(mockRunResponse);
  });

  it('should render the initial form elements', () => {
    render(<RecommendationsPage />);
    expect(screen.getByText('Recomendações (IA)')).toBeInTheDocument();
    expect(screen.getByLabelText('Tipo do run')).toBeInTheDocument();
    expect(screen.getByLabelText('Snapshot ID (opcional)')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Iniciar run de recomendações/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Consultar run/i })
    ).toBeInTheDocument();
  });

  it('should call createRecommendationRun with correct payload on form submission', async () => {
    render(<RecommendationsPage />);

    // Fill out the form
    fireEvent.change(screen.getByLabelText('Tipo do run'), {
      target: { value: 'churn' },
    });
    fireEvent.change(screen.getByLabelText('Snapshot ID (opcional)'), {
      target: { value: 'snap-456' },
    });

    // Submit the form
    fireEvent.click(
      screen.getByRole('button', { name: /Iniciar run de recomendações/i })
    );

    await waitFor(() => {
      expect(mockCreateRecommendationRun).toHaveBeenCalledTimes(1);
    });

    expect(mockCreateRecommendationRun).toHaveBeenCalledWith(
      'test-tenant',
      'test-token',
      expect.objectContaining({
        runType: 'churn',
        snapshotId: 'snap-456',
      })
    );

    // Check if the job status is displayed
    expect(await screen.findByText('Status do job')).toBeInTheDocument();
    expect(screen.getByText('job-123')).toBeInTheDocument();
  });

  it('should call getRecommendationRun when "Consultar run" is clicked', async () => {
    render(<RecommendationsPage />);

    // Set a runId to fetch
    fireEvent.change(screen.getByLabelText('Run ID'), {
      target: { value: 'job-123' },
    });

    // Click the fetch button
    fireEvent.click(screen.getByRole('button', { name: /Consultar run/i }));

    await waitFor(() => {
      expect(mockGetRecommendationRun).toHaveBeenCalledTimes(1);
    });

    expect(mockGetRecommendationRun).toHaveBeenCalledWith(
      'test-tenant',
      'job-123',
      'test-token'
    );

    // Check if the run details are displayed
    expect(await screen.findByText('Detalhes do run')).toBeInTheDocument();
    expect(screen.getByText('Recommendation 1')).toBeInTheDocument();
  });

  it('should display an error if starting a run fails', async () => {
    mockCreateRecommendationRun.mockRejectedValue(
      new Error('Failed to start run.')
    );
    render(<RecommendationsPage />);

    fireEvent.click(
      screen.getByRole('button', { name: /Iniciar run de recomendações/i })
    );

    expect(await screen.findByText('Failed to start run.')).toBeInTheDocument();
  });

  it('should display an error if fetching a run fails', async () => {
    mockGetRecommendationRun.mockRejectedValue(
      new Error('Failed to fetch run.')
    );
    render(<RecommendationsPage />);

    fireEvent.change(screen.getByLabelText('Run ID'), {
      target: { value: 'job-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Consultar run/i }));

    expect(await screen.findByText('Failed to fetch run.')).toBeInTheDocument();
  });

  it('should show loading state on start button', () => {
    mockCreateRecommendationRun.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<RecommendationsPage />);

    fireEvent.click(
      screen.getByRole('button', { name: /Iniciar run de recomendações/i })
    );

    expect(
      screen.getByRole('button', { name: /Enviando.../i })
    ).toBeInTheDocument();
  });

  it('should show fetching state on consult button', () => {
    mockGetRecommendationRun.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<RecommendationsPage />);

    fireEvent.change(screen.getByLabelText('Run ID'), {
      target: { value: 'job-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Consultar run/i }));

    expect(
      screen.getByRole('button', { name: /Consultando.../i })
    ).toBeInTheDocument();
  });
});
