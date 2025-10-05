import { FormEvent, useState, useCallback } from 'react';

import { createRecommendationRun, getRecommendationRun } from '../api/recommendations';
import type { CalculationJobStatus, RecommendationRunResponse } from '../api/types';
import { useAuth } from './useAuth';

export const useRecommendations = () => {
  const { tenantId, accessToken } = useAuth();
  const [runType, setRunType] = useState('pricing');
  const [snapshotId, setSnapshotId] = useState('');
  const [simulationId, setSimulationId] = useState('');
  const [parameters, setParameters] = useState(
    JSON.stringify(
      {
        target: 'inadimplencia',
      },
      null,
      2,
    ),
  );
  const [jobStatus, setJobStatus] = useState<CalculationJobStatus | null>(null);
  const [runDetail, setRunDetail] = useState<RecommendationRunResponse | null>(null);
  const [runId, setRunId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);

  const handleStartRun = useCallback(
    async (event: FormEvent) => {
      event.preventDefault();
      if (!tenantId || !accessToken) {
        setError('Faça login para acessar recomendações.');
        return;
      }
      setError(null);
      let parsedParams: Record<string, unknown> | undefined;
      if (parameters.trim()) {
        try {
          parsedParams = JSON.parse(parameters);
        } catch (err) {
          setError('Parâmetros devem ser um JSON válido.');
          return;
        }
      }
      try {
        setLoading(true);
        const response = await createRecommendationRun(tenantId, accessToken, {
          runType,
          snapshotId: snapshotId || undefined,
          simulationId: simulationId || undefined,
          parameters: parsedParams,
        });
        setJobStatus(response);
        setRunId(response.jobId);
        setRunDetail(null);
      } catch (err) {
        const message = (err as Error).message ?? 'Falha ao iniciar recomendação (endpoint pode não estar disponível).';
        setError(message);
        setJobStatus(null);
      } finally {
        setLoading(false);
      }
    },
    [accessToken, parameters, runType, simulationId, snapshotId, tenantId],
  );

  const handleFetchRun = useCallback(async () => {
    if (!tenantId || !accessToken) {
      setError('Faça login para acessar recomendações.');
      return;
    }
    setError(null);
    if (!runId) {
      setError('Informe o runId retornado pelo backend.');
      return;
    }
    try {
      setFetching(true);
      const response = await getRecommendationRun(tenantId, runId, accessToken);
      setRunDetail(response);
    } catch (err) {
      const message = (err as Error).message ?? 'Não foi possível buscar o run (endpoint pode não existir).';
      setError(message);
    } finally {
      setFetching(false);
    }
  }, [accessToken, runId, tenantId]);

  return {
    runType, setRunType,
    snapshotId, setSnapshotId,
    simulationId, setSimulationId,
    parameters, setParameters,
    jobStatus,
    runDetail,
    runId, setRunId,
    error,
    loading,
    fetching,
    handleStartRun,
    handleFetchRun,
  };
};