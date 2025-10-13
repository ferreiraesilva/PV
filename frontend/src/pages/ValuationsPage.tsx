import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { useValuations } from '../hooks/useValuations';
import { evaluateValuation } from '../api/valuations';
import type {
  ValuationCashflowInput,
  ValuationResponse,
  ValuationScenarioInput,
} from '../api/types';
import './ValuationsPage.css';

export default function ValuationsPage() {
  const { tenantId, accessToken } = useAuth();
  const {
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
  } = useValuations();

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Autentique-se para executar valuations.</p>
      </div>
    );
  }

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
          <small>
            Use o identificador de snapshot utilizado nas rotinas de valuations
            (UUID).
          </small>
        </div>
        <section className="cashflows">
          <header>
            <h2>Fluxos de caixa</h2>
            <button
              type="button"
              className="button ghost"
              onClick={addCashflow}
            >
              Adicionar fluxo
            </button>
          </header>
          <div className="table-responsive">
            <table className="table editable-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Valor</th>
                  <th>Prob. Default</th>
                  <th>Prob. Cancel.</th>
                  <th style={{ width: '50px' }}></th>
                </tr>
              </thead>
              <tbody>
                {cashflows.map((item, index) => (
                  <tr key={`cashflow-${index}`}>
                    <td>
                      <input
                        type="date"
                        value={item.due_date}
                        onChange={(event) =>
                          updateCashflow(
                            index,
                            'due_date',
                            event.target.value as string
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.amount}
                        onChange={(event) =>
                          updateCashflow(
                            index,
                            'amount',
                            event.target.valueAsNumber || 0
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.001"
                        value={item.probability_default}
                        onChange={(event) =>
                          updateCashflow(
                            index,
                            'probability_default',
                            event.target.valueAsNumber || 0
                          )
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.001"
                        value={item.probability_cancellation}
                        onChange={(event) =>
                          updateCashflow(
                            index,
                            'probability_cancellation',
                            event.target.valueAsNumber || 0
                          )
                        }
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="remove"
                        onClick={() => removeCashflow(index)}
                        disabled={cashflows.length === 1}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section className="scenarios">
          <header>
            <h2>Cenários</h2>
            <button
              type="button"
              className="button ghost"
              onClick={addScenario}
            >
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
                    onChange={(event) =>
                      updateScenario(
                        index,
                        'code',
                        event.target.value as string
                      )
                    }
                  />
                </div>
                <div className="form-field">
                  <label>Taxa de desconto</label>
                  <input
                    type="number"
                    min="0"
                    step="0.0001"
                    value={scenario.discount_rate}
                    onChange={(event) =>
                      updateScenario(
                        index,
                        'discount_rate',
                        event.target.valueAsNumber || 0
                      )
                    }
                  />
                </div>
                <div className="form-field">
                  <label>Multiplicador default</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={scenario.default_multiplier}
                    onChange={(event) =>
                      updateScenario(
                        index,
                        'default_multiplier',
                        event.target.valueAsNumber || 0
                      )
                    }
                  />
                </div>
                <div className="form-field">
                  <label>Multiplicador cancelamento</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={scenario.cancellation_multiplier}
                    onChange={(event) =>
                      updateScenario(
                        index,
                        'cancellation_multiplier',
                        event.target.valueAsNumber || 0
                      )
                    }
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
                  <td>
                    {item.gross_present_value.toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </td>
                  <td>
                    {item.net_present_value.toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </td>
                  <td>
                    {item.expected_losses.toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
