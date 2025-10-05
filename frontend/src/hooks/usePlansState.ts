import { useCallback, useState } from 'react';
import { produce } from 'immer';

interface InstallmentRow {
  due_date: string;
  amount: number;
}

type AdjustmentPeriodicity = 'monthly' | 'anniversary';

export interface PlanFormState {
  key: string;
  label: string;
  productCode: string;
  principal: number;
  discountRate: number;
  discountRatePeriod: 'monthly' | 'annual';
  baseDate: string;
  adjustmentIndex?: 'INCC' | 'IGPM' | 'IPCA' | 'CUSTOM';
  adjustmentPeriodicity: AdjustmentPeriodicity;
  adjustmentAddonRate: number;
  installments: InstallmentRow[];
}

const addMonths = (date: Date, months: number): Date => {
  const d = new Date(date);
  d.setMonth(d.getMonth() + months);
  return d;
};

export const usePlansState = (initialPlans: PlanFormState[]) => {
  const [plans, setPlans] = useState<PlanFormState[]>(initialPlans);

  const updatePlanField = useCallback((planIndex: number, field: keyof Omit<PlanFormState, 'installments' | 'key'>, value: string | number) => {
    setPlans(produce(draft => {
      (draft[planIndex] as any)[field] = value;
    }));
  }, []);

  const updateInstallment = useCallback((planIndex: number, installmentIndex: number, field: keyof InstallmentRow, value: string | number) => {
    setPlans(produce(draft => {
      (draft[planIndex].installments[installmentIndex] as any)[field] = value;
    }));
  }, []);

  const addInstallment = useCallback((planIndex: number) => {
    setPlans(produce(draft => {
      const installments = draft[planIndex].installments;
      const lastInstallment = installments[installments.length - 1];
      const lastDate = lastInstallment ? new Date(lastInstallment.due_date) : new Date();
      const newDate = addMonths(lastDate, 1);
      installments.push({ due_date: newDate.toISOString().slice(0, 10), amount: lastInstallment?.amount ?? 1000 });
    }));
  }, []);

  const removeInstallment = useCallback((planIndex: number, installmentIndex: number) => {
    setPlans(produce(draft => {
      draft[planIndex].installments.splice(installmentIndex, 1);
    }));
  }, []);

  return { plans, setPlans, updatePlanField, updateInstallment, addInstallment, removeInstallment };
};