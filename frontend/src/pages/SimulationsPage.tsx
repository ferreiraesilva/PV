import { FormEvent, useState } from 'react';

import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { createSimulation } from '../api/simulations';
import type { SimulationRequest, SimulationResponse } from '../api/types';
import './SimulationsPage.css';

interface InstallmentRow {
  period: number;
  amount: number;
}

const DEFAULT_INSTALLMENTS: InstallmentRow[] = [
  { period: 1, amount: 1000 },
  { period: 2, amount: 1000 },
  { period: 3, amount: 1000 },
];

export default function SimulationsPage() {
  const { tenantId, accessToken } = useAuth();
  const [principal, setPrincipal] = useState(3000);
  const [discountRate, setDiscountRate] = useState(0.015);
  const [installments, setInstallments] = useState<InstallmentRow[]>(DEFAULT_INSTALLMENTS);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Faça login para enviar simulações.</p>
      </div>
    );
  }

  const updateInstallment = (index: number, key: keyof InstallmentRow, value: number) => {
    setInstallments((rows) => {
      const next = [...rows];
      next[index] = { ...next[index], [key]: value };
      return next;
    });
  };

  const addInstallment = () => {
    setInstallments((rows) => [
      ...rows,
      {
        period: rows.length ? rows[rows.length - 1].period + 1 : 1,
        amount: rows.length ? rows[rows.length - 1].amount : 1000,
      },
    ]);
  };

  const removeInstallment = (index: number) => {
    setInstallments((rows) => rows.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!installments.length) {
      setError('Inclua pelo menos uma parcela.');
      return;
    }
    const payload: SimulationRequest = {
      principal: Number(principal),
      discount_rate: Number(discountRate),
      installments: installments.map((item) => ({
        period: Number(item.period),
        amount: Number(item.amount),
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

  return (
    <div className="stack">
      <PageHeader
        title="Simulações financeiras"
        subtitle="Monte planos de pagamento e avalie métricas-chave automaticamente."
      />
      <form className="card stack" onSubmit={handleSubmit}>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="principal">Valor total (principal)</label>
            <input
              id="principal"
              type="number"
              min="0"
              step="0.01"
              value={principal}
              onChange={(event) => setPrincipal(Number(event.target.value))}
            />
          </div>
          <div className="form-field">
            <label htmlFor="discountRate">Taxa de desconto mensal</label>
            <input
              id="discountRate"
              type="number"
              min="0"
              step="0.0001"
              value={discountRate}
              onChange={(event) => setDiscountRate(Number(event.target.value))}
            />
            <small>Use valores decimais. Ex.: 0.015 = 1.5% ao mês.</small>
          </div>
        </div>
        <section className="installments">
          <header>
            <h2>Parcelas</h2>
            <button type="button" className="button ghost" onClick={addInstallment}>
              Adicionar parcela
            </button>
          </header>
          <div className="installments-grid">
            {installments.map((item, index) => (
              <div key={`installment-${index}`} className="installment-row">
                <div className="form-field">
                  <label>Período</label>
                  <input
                    type="number"
                    min="1"
                    value={item.period}
                    onChange={(event) => updateInstallment(index, 'period', Number(event.target.value))}
                  />
                </div>
                <div className="form-field">
                  <label>Valor</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={item.amount}
                    onChange={(event) => updateInstallment(index, 'amount', Number(event.target.value))}
                  />
                </div>
                <button
                  type="button"
                  className="remove"
                  onClick={() => removeInstallment(index)}
                  aria-label="Remover parcela"
                  disabled={installments.length === 1}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </section>
        {error && <div className="alert error">{error}</div>}
        <button className="button" type="submit" disabled={submitting}>
          {submitting ? 'Calculando...' : 'Calcular plano'}
        </button>
      </form>
      {result && (
        <section className="card simulation-result">
          <header>
            <h2>Resultado</h2>
            <span className="badge">PV = {result.result.present_value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>
          </header>
          <div className="grid two">
            <div>
              <span className="label">Valor Futuro (FV)</span>
              <p className="value">
                {result.result.future_value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </p>
            </div>
            <div>
              <span className="label">Parcela equivalente (PMT)</span>
              <p className="value">
                {result.result.payment.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </p>
            </div>
            <div>
              <span className="label">Parcela média</span>
              <p className="value">
                {result.result.average_installment.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </p>
            </div>
            <div>
              <span className="label">Prazo médio (meses)</span>
              <p className="value">{result.result.mean_term_months.toFixed(2)}</p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
