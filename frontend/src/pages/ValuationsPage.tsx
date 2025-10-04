import { FormEvent, useState } from 'react';

import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { evaluateValuation } from '../api/valuations';
import type { ValuationCashflowInput, ValuationResponse, ValuationScenarioInput } from '../api/types';
import './ValuationsPage.css';

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
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
    amount: 12000,
    probability_default: 0.07,
    probability_cancellation: 0.015,
  },
];

const DEFAULT_SCENARIOS: ScenarioRow[] = [
  { code: 'optimista', discount_rate: 0.01, default_multiplier: 0.8, cancellation_multiplier: 0.7 },
  { code: 'base', discount_rate: 0.015, default_multiplier: 1, cancellation_multiplier: 1 },
  { code: 'conservador', discount_rate: 0.02, default_multiplier: 1.2, cancellation_multiplier: 1.3 },
];

export default function ValuationsPage() {
  const { tenantId, accessToken } = useAuth();
  const [snapshotId, setSnapshotId] = useState('');
  const [cashflows, setCashflows] = useState<CashflowRow[]>(DEFAULT_CASHFLOWS);
  const [scenarios, setScenarios] = useState<ScenarioRow[]>(DEFAULT_SCENARIOS);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ValuationResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Autentique-se para executar valuations.</p>
      </div>
    );
  }

  const updateCashflow = (index: number, key: keyof CashflowRow, value: string) => {
    setCashflows((rows) => {
      const next = [...rows];
      const parsedValue = key === 'due_date' ? value : Number(value);
      next[index] = { ...next[index], [key]: parsedValue };
      return next;
    });
  };

  const addCashflow = () => {
    setCashflows((rows) => [
      ...rows,
      {
        due_date: new Date().toISOString().slice(0, 10),
        amount: 10000,
        probability_default: 0.05,
        probability_cancellation: 0.02,
      },
    ]);
  };

  const removeCashflow = (index: number) => {
    setCashflows((rows) => rows.filter((_, idx) => idx !== index));
  };

  const updateScenario = (index: number, key: keyof ScenarioRow, value: string) => {
    setScenarios((rows) => {
      const next = [...rows];
      next[index] = { ...next[index], [key]: key === 'code' ? value : Number(value) };
      return next;
    });
  };

  const addScenario = () => {
    setScenarios((rows) => [
      ...rows,
      {
        code: `cenario-${rows.length + 1}`,
        discount_rate: 0.02,
        default_multiplier: 1,
        cancellation_multiplier: 1,
      },
    ]);
  };

  const removeScenario = (index: number) => {
    setScenarios((rows) => rows.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!snapshotId) {
      setError('Informe o snapshotId que será usado como referência.');
      return;
    }
    if (!cashflows.length || !scenarios.length) {
      setError('Cadastre ao menos um fluxo de caixa e um cenário.');
      return;
    }

    try {
      setSubmitting(true);
      const response = await evaluateValuation(tenantId, snapshotId, accessToken, {
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

  return (
    <div className="stack">
      <PageHeader
        title="Valuation de carteira"
        subtitle="Combine fluxos de recebíveis com múltiplos cenários de risco para estimar VPB e VPL."
      />
      <form className="card stack" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="snapshotId">Snapshot ID</label>
          <input
            id="snapshotId"
            value={snapshotId}
            onChange={(event) => setSnapshotId(event.target.value)}
            placeholder="UUID do snapshot"
          />
          <small>Use o identificador de snapshot utilizado nas rotinas de valuations (UUID).</small>
        </div>
        <section className="cashflows">
          <header>
            <h2>Fluxos de caixa</h2>
            <button type="button" className="button ghost" onClick={addCashflow}>
              Adicionar fluxo
            </button>
          </header>
          <div className="cashflow-grid">
            {cashflows.map((item, index) => (
              <div key={`cashflow-${index}`} className="cashflow-row">
                <div className="form-field">
                  <label>Data</label>
                  <input
                    type="date"
                    value={item.due_date}
                    onChange={(event) => updateCashflow(index, 'due_date', event.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Valor</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={item.amount}
                    onChange={(event) => updateCashflow(index, 'amount', event.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Prob. default</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.001"
                    value={item.probability_default}
                    onChange={(event) => updateCashflow(index, 'probability_default', event.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Prob. cancelamento</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.001"
                    value={item.probability_cancellation}
                    onChange={(event) => updateCashflow(index, 'probability_cancellation', event.target.value)}
                  />
                </div>
                <button
                  type="button"
                  className="remove"
                  onClick={() => removeCashflow(index)}
                  disabled={cashflows.length === 1}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </section>
        <section className="scenarios">
          <header>
            <h2>Cenários</h2>
            <button type="button" className="button ghost" onClick={addScenario}>
              Adicionar cenário
            </button>
          </header>
          <div className="scenario-grid">
            {scenarios.map((scenario, index) => (
              <div key={`scenario-${index}`} className="scenario-row">
                <div className="form-field">
                  <label>Identificador</label>
                  <input
                    value={scenario.code}
                    onChange={(event) => updateScenario(index, 'code', event.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Taxa de desconto</label>
                  <input
                    type="number"
                    min="0"
                    step="0.0001"
                    value={scenario.discount_rate}
                    onChange={(event) => updateScenario(index, 'discount_rate', event.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Multiplicador default</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={scenario.default_multiplier}
                    onChange={(event) => updateScenario(index, 'default_multiplier', event.target.value)}
                  />
                </div>
                <div className="form-field">
                  <label>Multiplicador cancelamento</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={scenario.cancellation_multiplier}
                    onChange={(event) => updateScenario(index, 'cancellation_multiplier', event.target.value)}
                  />
                </div>
                <button
                  type="button"
                  className="remove"
                  onClick={() => removeScenario(index)}
                  disabled={scenarios.length === 1}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </section>
        {error && <div className="alert error">{error}</div>}
        <button className="button" type="submit" disabled={submitting}>
          {submitting ? 'Executando...' : 'Executar cenários'}
        </button>
      </form>
      {result && (
        <section className="card valuation-result">
          <header>
            <h2>Resultados consolidados</h2>
            <p>Comparação entre cenários submetidos.</p>
          </header>
          <table className="table">
            <thead>
              <tr>
                <th>Cenário</th>
                <th>VP Bruto</th>
                <th>VP Líquido</th>
                <th>Perdas esperadas</th>
              </tr>
            </thead>
            <tbody>
              {result.results.map((item) => (
                <tr key={item.code}>
                  <td>{item.code}</td>
                  <td>{item.gross_present_value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                  <td>{item.net_present_value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                  <td>{item.expected_losses.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
