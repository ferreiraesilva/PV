import { FormEvent, useState, useCallback } from 'react';
import { produce } from 'immer';

import { evaluateValuation } from '../api/valuations';
import type {
  ValuationCashflowInput,
  ValuationResponse,
  ValuationScenarioInput,
} from '../api/types';
import { useAuth } from './useAuth';

type CashflowRow = ValuationCashflowInput;
type ScenarioRow = ValuationScenarioInput;

const DEFAULT_CASHFLOWS: CashflowRow[] = [
  {
    due_date: new Date().toISOString().slice(0, 10),
    amount: 15000,
    probability_default: 0.05,
    probability_cancellation: 0.02,
  },
  {
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10),
    amount: 12000,
    probability_default: 0.07,
    probability_cancellation: 0.015,
  },
];

const DEFAULT_SCENARIOS: ScenarioRow[] = [
  {
    code: 'optimista',
    discount_rate: 0.01,
    default_multiplier: 0.8,
    cancellation_multiplier: 0.7,
  },
  {
    code: 'base',
    discount_rate: 0.015,
    default_multiplier: 1,
    cancellation_multiplier: 1,
  },
  {
    code: 'conservador',
    discount_rate: 0.02,
    default_multiplier: 1.2,
    cancellation_multiplier: 1.3,
  },
];

export const useValuations = () => {
  const { tenantId, accessToken } = useAuth();
  const [snapshotId, setSnapshotId] = useState('');
  const [cashflows, setCashflows] = useState<CashflowRow[]>(DEFAULT_CASHFLOWS);
  const [scenarios, setScenarios] = useState<ScenarioRow[]>(DEFAULT_SCENARIOS);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ValuationResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const updateCashflow = useCallback(
    (index: number, key: keyof CashflowRow, value: string | number) => {
      setCashflows(
        produce((draft) => {
          (draft[index] as any)[key] = value;
        })
      );
    },
    []
  );

  const addCashflow = useCallback(() => {
    setCashflows(
      produce((draft) => {
        draft.push({
          due_date: new Date().toISOString().slice(0, 10),
          amount: 10000,
          probability_default: 0.05,
          probability_cancellation: 0.02,
        });
      })
    );
  }, []);

  const removeCashflow = useCallback((index: number) => {
    setCashflows(
      produce((draft) => {
        draft.splice(index, 1);
      })
    );
  }, []);

  const updateScenario = useCallback(
    (index: number, key: keyof ScenarioRow, value: string | number) => {
      setScenarios(
        produce((draft) => {
          (draft[index] as any)[key] = value;
        })
      );
    },
    []
  );

  const addScenario = useCallback(() => {
    setScenarios(
      produce((draft) => {
        draft.push({
          code: `cenario-${draft.length + 1}`,
          discount_rate: 0.02,
          default_multiplier: 1,
          cancellation_multiplier: 1,
        });
      })
    );
  }, []);

  const removeScenario = useCallback((index: number) => {
    setScenarios(
      produce((draft) => {
        draft.splice(index, 1);
      })
    );
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!tenantId || !accessToken) {
      setError('Sessão inválida. Por favor, autentique-se novamente.');
      return;
    }
    if (!snapshotId) {
      setError('Informe o snapshotId que será usado como referência.');
      return;
    }
    if (!cashflows.length || !scenarios.length) {
      setError('Cadastre ao menos um fluxo de caixa e um cenário.');
      return;
    }

    // Validação de códigos de cenários duplicados (ignorando códigos vazios)
    const scenarioCodes = scenarios
      .map((s) => s.code.trim())
      .filter((code) => code !== '');
    if (scenarioCodes.length > new Set(scenarioCodes).size) {
      setError(
        'Não são permitidos cenários com códigos duplicados. Por favor, ajuste os códigos e tente novamente.'
      );
      return;
    }

    try {
      setSubmitting(true);
      const response = await evaluateValuation(tenantId, accessToken, {
        cashflows,
        scenarios,
      });
      setResult(response);
    } catch (err) {
      const message = (err as Error).message ?? 'Erro ao executar valuation.';
      setError(message);
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  };

  return {
    snapshotId,
    setSnapshotId,
    cashflows,
    updateCashflow,
    addCashflow,
    removeCashflow,
    scenarios,
    updateScenario,
    addScenario,
    removeScenario,
    error,
    result,
    submitting,
    handleSubmit,
  };
};
