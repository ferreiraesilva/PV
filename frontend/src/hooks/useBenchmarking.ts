import { FormEvent, useState } from 'react';

import { ingestBenchmarkDataset, listBenchmarkAggregations } from '../api/benchmarking';
import type { BenchmarkAggregationItem, BenchmarkAggregationsResponse, BenchmarkIngestResponse } from '../api/types';
import { useAuth } from './useAuth'; // Assuming useAuth is in the same hooks directory

interface AggregationState {
  batchId: string;
  rows: BenchmarkAggregationItem[];
  totalRows?: number;
  discardedRows?: number;
}

export const useBenchmarking = () => {
  const { tenantId, accessToken } = useAuth();
  const [batchId, setBatchId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [aggregation, setAggregation] = useState<AggregationState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);

  const handleFileChange = (event: FormEvent<HTMLInputElement>) => {
    const input = event.currentTarget;
    setFile(input.files && input.files.length > 0 ? input.files[0] : null);
  };

  const handleIngest = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!tenantId || !accessToken) {
      setError('Sessão inválida. Por favor, autentique-se novamente.');
      return;
    }
    if (!batchId) {
      setError('Informe o batchId que será vinculado ao dataset.');
      return;
    }
    if (!file) {
      setError('Selecione um arquivo CSV ou XLSX.');
      return;
    }

    try {
      setLoading(true);
      const response: BenchmarkIngestResponse = await ingestBenchmarkDataset(tenantId, batchId, accessToken, file);
      setAggregation({
        batchId: response.batchId,
        rows: response.aggregations,
        totalRows: response.totalRows,
        discardedRows: response.discardedRows,
      });
    } catch (err) {
      const message = (err as Error).message ?? 'Falha ao processar dataset.';
      setError(message);
      setAggregation(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchAggregations = async () => {
    if (!tenantId || !accessToken || !batchId) {
      setError('Informe o batchId para consultar agregações.');
      return;
    }
    setError(null);
    try {
      setFetching(true);
      const response: BenchmarkAggregationsResponse = await listBenchmarkAggregations(tenantId, batchId, accessToken);
      setAggregation({ batchId: response.batchId, rows: response.aggregations });
    } catch (err) {
      const message = (err as Error).message ?? 'Não foi possível recuperar agregações.';
      setError(message);
    } finally {
      setFetching(false);
    }
  };

  return { batchId, setBatchId, aggregation, error, loading, fetching, handleFileChange, handleIngest, fetchAggregations };
};