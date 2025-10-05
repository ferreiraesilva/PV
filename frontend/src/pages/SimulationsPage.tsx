import { FormEvent, useMemo, useState } from 'react';

import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { createSimulation } from '../api/simulations';
import type { SimulationBatchRequest, SimulationBatchResponse, SimulationOutcome } from '../api/types';
import './SimulationsPage.css';

interface InstallmentRow {
  period: number;
  amount: number;
}

interface PlanFormState {
  key: string;
  label: string;
  productCode: string;
  principal: number;
  discountRate: number;
  installments: InstallmentRow[];
}

const createDefaultInstallments = (): InstallmentRow[] => [
  { period: 1, amount: 1000 },
  { period: 2, amount: 1000 },
  { period: 3, amount: 1000 },
];

const createPlanState = (index: number): PlanFormState => ({
  key: `plan-${Date.now()}-${index}`,
  label: '',
  productCode: '',
  principal: 3000,
  discountRate: 0.015,
  installments: createDefaultInstallments(),
});

const formatCurrency = (value: number): string =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const formatMonths = (value: number): string => value.toFixed(2);

export default function SimulationsPage() {
  const { tenantId, accessToken } = useAuth();
  const [plans, setPlans] = useState<PlanFormState[]>([createPlanState(0)]);
  const [result, setResult] = useState<SimulationBatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canRemovePlan = useMemo(() => plans.length > 1, [plans.length]);

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Faça login para enviar simulações.</p>
      </div>
    );
  }

  const updatePlanField = (planIndex: number, field: keyof Omit<PlanFormState, 'installments' | 'key'>, value: string | number) => {
    setPlans((current) => {
      const next = [...current];
      const plan = { ...next[planIndex] };
      if (field === 'principal' || field === 'discountRate') {
        plan[field] = Number(value);
      } else {
        plan[field] = value as string;
      }
      next[planIndex] = plan;
      return next;
    });
  };

  const updateInstallment = (planIndex: number, installmentIndex: number, field: keyof InstallmentRow, value: number) => {
    setPlans((current) => {
      const next = [...current];
      const plan = { ...next[planIndex] };
      const installments = [...plan.installments];
      installments[installmentIndex] = { ...installments[installmentIndex], [field]: value };
      plan.installments = installments;
      next[planIndex] = plan;
      return next;
    });
  };

  const addInstallment = (planIndex: number) => {
    setPlans((current) => {
      const next = [...current];
      const plan = { ...next[planIndex] };
      const installments = [...plan.installments];
      const last = installments[installments.length - 1];
      installments.push({
        period: last ? last.period + 1 : 1,
        amount: last ? last.amount : 1000,
      });
      plan.installments = installments;
      next[planIndex] = plan;
      return next;
    });
  };

  const removeInstallment = (planIndex: number, installmentIndex: number) => {
    setPlans((current) => {
      const next = [...current];
      const plan = { ...next[planIndex] };
      plan.installments = plan.installments.filter((_, idx) => idx !== installmentIndex);
      next[planIndex] = plan;
      return next;
    });
  };

  const addPlan = () => {
    setPlans((current) => [...current, createPlanState(current.length + 1)]);
    setResult(null);
  };

  const removePlan = (planIndex: number) => {
    if (!canRemovePlan) {
      return;
    }
    setPlans((current) => current.filter((_, index) => index !== planIndex));
    setResult(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!plans.length) {
      setError('Inclua pelo menos um plano para simular.');
      return;
    }

    if (plans.some((plan) => plan.installments.length === 0)) {
      setError('Inclua pelo menos uma parcela em cada plano.');
      return;
    }

    const payload: SimulationBatchRequest = {
      plans: plans.map((plan) => ({
        key: plan.key,
        label: plan.label.trim() || undefined,
        product_code: plan.productCode.trim() || undefined,
        principal: Number(plan.principal),
        discount_rate: Number(plan.discountRate),
        installments: plan.installments.map((item) => ({
          period: Number(item.period),
          amount: Number(item.amount),
        })),
      })),
    };

    try {
      setSubmitting(true);
      const response = await createSimulation(tenantId, accessToken, payload);
      setResult(response);
    } catch (err) {
      const message = (err as Error).message ?? 'Erro ao calcular simulação.';
      setError(message);
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  };

  const renderOutcomeRow = (item: SimulationOutcome, index: number) => {
    const label = item.label ?? (item.source === 'template' ? 'Plano padronizado' : `Plano ${index + 1}`);
    const product = item.product_code ?? '—';
    const key = `${item.source}-${item.template_id ?? item.plan_key ?? index}`;

    return (
      <tr key={key}>
        <td>{item.source === 'template' ? 'Padronizado' : 'Informado'}</td>
        <td>{label}</td>
        <td>{product}</td>
        <td>{formatCurrency(item.result.present_value)}</td>
        <td>{formatCurrency(item.result.future_value)}</td>
        <td>{formatCurrency(item.result.payment)}</td>
        <td>{formatCurrency(item.result.average_installment)}</td>
        <td>{formatMonths(item.result.mean_term_months)}</td>
      </tr>
    );
  };

  return (
    <div className="stack">
      <PageHeader
        title="Simulações financeiras"
        subtitle="Monte e compare planos de pagamento informados e padronizados em uma única chamada."
      />
      <form className="card stack" onSubmit={handleSubmit}>
        <div className="form-actions">
          <button type="button" className="button ghost" onClick={addPlan}>
            Adicionar plano
          </button>
        </div>
        {plans.map((plan, planIndex) => (
          <section key={plan.key} className="stack plan-section">
            <header className="plan-header">
              <h2>Plano {planIndex + 1}</h2>
              <div className="plan-controls">
                <button
                  type="button"
                  className="button ghost"
                  onClick={() => addInstallment(planIndex)}
                >
                  Adicionar parcela
                </button>
                <button
                  type="button"
                  className="button ghost"
                  onClick={() => removePlan(planIndex)}
                  disabled={!canRemovePlan}
                >
                  Remover plano
                </button>
              </div>
            </header>
            <div className="grid three">
              <div className="form-field">
                <label htmlFor={`label-${plan.key}`}>Nome do plano</label>
                <input
                  id={`label-${plan.key}`}
                  type="text"
                  value={plan.label}
                  maxLength={64}
                  onChange={(event) => updatePlanField(planIndex, 'label', event.target.value)}
                  placeholder="Ex.: Oferta especial"
                />
              </div>
              <div className="form-field">
                <label htmlFor={`product-${plan.key}`}>Produto (código)</label>
                <input
                  id={`product-${plan.key}`}
                  type="text"
                  value={plan.productCode}
                  maxLength={128}
                  onChange={(event) => updatePlanField(planIndex, 'productCode', event.target.value)}
                  placeholder="Ex.: APTO-101"
                />
                <small>Informe para comparar com o plano padronizado correspondente.</small>
              </div>
            </div>
            <div className="grid two">
              <div className="form-field">
                <label htmlFor={`principal-${plan.key}`}>Valor total (principal)</label>
                <input
                  id={`principal-${plan.key}`}
                  type="number"
                  min="0"
                  step="0.01"
                  value={plan.principal}
                  onChange={(event) => updatePlanField(planIndex, 'principal', Number(event.target.value))}
                />
              </div>
              <div className="form-field">
                <label htmlFor={`discount-${plan.key}`}>Taxa de desconto mensal</label>
                <input
                  id={`discount-${plan.key}`}
                  type="number"
                  min="0"
                  step="0.0001"
                  value={plan.discountRate}
                  onChange={(event) => updatePlanField(planIndex, 'discountRate', Number(event.target.value))}
                />
                <small>Use valores decimais. Ex.: 0.015 = 1.5% ao mês.</small>
              </div>
            </div>
            <div className="installments">
              <h3>Parcelas</h3>
              <div className="installments-grid">
                {plan.installments.map((item, installmentIndex) => (
                  <div key={`installment-${plan.key}-${installmentIndex}`} className="installment-row">
                    <div className="form-field">
                      <label>Período</label>
                      <input
                        type="number"
                        min="1"
                        value={item.period}
                        onChange={(event) =>
                          updateInstallment(planIndex, installmentIndex, 'period', Number(event.target.value))
                        }
                      />
                    </div>
                    <div className="form-field">
                      <label>Valor</label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.amount}
                        onChange={(event) =>
                          updateInstallment(planIndex, installmentIndex, 'amount', Number(event.target.value))
                        }
                      />
                    </div>
                    <button
                      type="button"
                      className="remove"
                      onClick={() => removeInstallment(planIndex, installmentIndex)}
                      aria-label="Remover parcela"
                      disabled={plan.installments.length === 1}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </section>
        ))}
        {error && <div className="alert error">{error}</div>}
        <button className="button" type="submit" disabled={submitting}>
          {submitting ? 'Calculando...' : 'Calcular comparativo'}
        </button>
      </form>
      {result && (
        <section className="card simulation-result">
          <header>
            <h2>Resultado comparativo</h2>
            <span className="badge">{result.outcomes.length} combinação(ões)</span>
          </header>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Origem</th>
                  <th>Plano</th>
                  <th>Produto</th>
                  <th>PV</th>
                  <th>FV</th>
                  <th>PMT</th>
                  <th>Parcela média</th>
                  <th>Prazo médio (meses)</th>
                </tr>
              </thead>
              <tbody>{result.outcomes.map(renderOutcomeRow)}</tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

