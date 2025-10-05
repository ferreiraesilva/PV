import { FormEvent, useMemo, useState } from 'react';

import { createSimulation } from '../api/simulations';
import type { SimulationBatchRequest, SimulationBatchResponse } from '../api/types';
import { useAuth } from './useAuth';
import { PlanFormState, usePlansState } from './usePlansState';

interface InstallmentRow {
  due_date: string;
  amount: number;
}

const addMonths = (date: Date, months: number): Date => {
  const d = new Date(date);
  d.setMonth(d.getMonth() + months);
  return d;
};

const createDefaultInstallments = (): InstallmentRow[] => {
  const today = new Date();
  return [
    { due_date: addMonths(today, 1).toISOString().slice(0, 10), amount: 1000 },
    { due_date: addMonths(today, 2).toISOString().slice(0, 10), amount: 1000 },
    { due_date: addMonths(today, 3).toISOString().slice(0, 10), amount: 1000 },
  ];
};

const createPlanState = (index: number): PlanFormState => ({
  key: `plan-${Date.now()}-${index}`,
  label: '',
  productCode: '',
  principal: 3000,
  discountRate: 1.5,
  discountRatePeriod: 'monthly',
  baseDate: new Date().toISOString().slice(0, 10),
  adjustmentIndex: 'INCC',
  adjustmentPeriodicity: 'monthly',
  adjustmentAddonRate: 1,
  installments: createDefaultInstallments(),
});

export const useSimulations = () => {
  const { tenantId, accessToken } = useAuth();
  const { plans, setPlans, ...planActions } = usePlansState([createPlanState(0)]);
  const [result, setResult] = useState<SimulationBatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canRemovePlan = useMemo(() => plans.length > 1, [plans.length]);

  const addPlan = () => {
    setPlans(current => [...current, createPlanState(current.length)]);
    setResult(null);
  };

  const removePlan = (planIndex: number) => {
    if (!canRemovePlan) return;
    setPlans(current => current.filter((_, index) => index !== planIndex));
    setResult(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!tenantId || !accessToken) {
      setError('Faça login para enviar simulações.');
      return;
    }
    if (!plans.length || plans.some(p => p.installments.length === 0)) {
      setError('Inclua pelo menos um plano com uma parcela para simular.');
      return;
    }

    const getMonthlyDecimalRate = (rate: number, period: 'monthly' | 'annual'): number => {
      const decimalRate = rate / 100;
      return period === 'monthly' ? decimalRate : Math.pow(1 + decimalRate, 1 / 12) - 1;
    };

    const payload: SimulationBatchRequest = {
      plans: plans.map(plan => ({
        ...plan,
        product_code: plan.productCode.trim() || undefined,
        discount_rate: getMonthlyDecimalRate(plan.discountRate, plan.discountRatePeriod),
        adjustment: plan.adjustmentIndex
          ? {
              base_date: plan.baseDate,
              index: plan.adjustmentIndex,
              periodicity: plan.adjustmentPeriodicity,
              addon_rate: plan.adjustmentAddonRate / 100,
            }
          : undefined,
      })),
    };

    try {
      setSubmitting(true);
      const response = await createSimulation(tenantId, accessToken, payload);
      setResult(response);
    } catch (err) {
      setError((err as Error).message ?? 'Erro ao calcular simulação.');
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  };

  return { ...planActions, plans, result, error, submitting, canRemovePlan, addPlan, removePlan, handleSubmit };
};