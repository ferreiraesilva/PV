import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { useSimulations } from '../hooks/useSimulations';
import type { SimulationOutcome } from '../api/types';
import './SimulationsPage.css';

const formatCurrency = (value: number): string =>
  value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const formatMonths = (value: number): string => value.toFixed(2);

export default function SimulationsPage() {
  const { tenantId, accessToken } = useAuth();
  const {
    plans,
    result,
    error,
    submitting,
    canRemovePlan,
    updatePlanField,
    updateInstallment,
    addInstallment,
    removeInstallment,
    addPlan,
    removePlan,
    handleSubmit,
  } = useSimulations();

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Faça login para enviar simulações.</p>
      </div>
    );
  }

  const renderOutcomeRow = (item: SimulationOutcome, index: number) => {
    const label =
      item.label ??
      (item.source === 'template' ? 'Plano padronizado' : `Plano ${index + 1}`);
    const product = item.product_code ?? '—';
    const key = `${item.source}-${item.template_id ?? item.plan_key ?? index}`;

    // Assuming the API response will be updated to include these fields
    const result = item.result as any;

    return (
      <tr key={key}>
        <td>{item.source === 'template' ? 'Padronizado' : 'Informado'}</td>
        <td>{label}</td>
        <td>{product}</td>
        <td>{formatCurrency(result.present_value)}</td>
        <td>
          {formatCurrency(
            result.present_value_adjusted ?? result.present_value
          )}
        </td>
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
                  onChange={(event) =>
                    updatePlanField(planIndex, 'label', event.target.value)
                  }
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
                  onChange={(event) =>
                    updatePlanField(
                      planIndex,
                      'productCode',
                      event.target.value
                    )
                  }
                  placeholder="Ex.: APTO-101"
                />
                <small>
                  Informe para comparar com o plano padronizado correspondente.
                </small>
              </div>
            </div>
            <div className="grid three">
              <div className="form-field">
                <label htmlFor={`principal-${plan.key}`}>
                  Valor total (principal)
                </label>
                <input
                  id={`principal-${plan.key}`}
                  type="number"
                  min="0"
                  step="0.01"
                  value={plan.principal}
                  onChange={(event) =>
                    updatePlanField(
                      planIndex,
                      'principal',
                      event.target.valueAsNumber || 0
                    )
                  }
                />
              </div>
              <div className="form-field-group">
                <div className="form-field">
                  <label htmlFor={`discount-${plan.key}`}>
                    Taxa de desconto (%)
                  </label>
                  <input
                    id={`discount-${plan.key}`}
                    type="number"
                    min="0"
                    step="0.01"
                    value={plan.discountRate}
                    onChange={(event) =>
                      updatePlanField(
                        planIndex,
                        'discountRate',
                        event.target.valueAsNumber || 0
                      )
                    }
                  />
                </div>
                <div className="form-field">
                  <label htmlFor={`period-${plan.key}`}>Período</label>
                  <select
                    id={`period-${plan.key}`}
                    value={plan.discountRatePeriod}
                    onChange={(event) =>
                      updatePlanField(
                        planIndex,
                        'discountRatePeriod',
                        event.target.value
                      )
                    }
                  >
                    <option value="monthly">Mensal</option>
                    <option value="annual">Anual</option>
                  </select>
                </div>
              </div>
              <div className="form-field">
                <label htmlFor={`base-date-${plan.key}`}>
                  Data base (reajuste)
                </label>
                <input
                  id={`base-date-${plan.key}`}
                  type="date"
                  value={plan.baseDate}
                  onChange={(event) =>
                    updatePlanField(planIndex, 'baseDate', event.target.value)
                  }
                />
              </div>
            </div>
            <div className="grid three">
              <div className="form-field">
                <label htmlFor={`adj-index-${plan.key}`}>
                  Índice de reajuste
                </label>
                <select
                  id={`adj-index-${plan.key}`}
                  value={plan.adjustmentIndex}
                  onChange={(event) =>
                    updatePlanField(
                      planIndex,
                      'adjustmentIndex',
                      event.target.value
                    )
                  }
                >
                  <option value="">Nenhum</option>
                  <option value="INCC">INCC</option>
                  <option value="IGPM">IGPM</option>
                  <option value="IPCA">IPCA</option>
                  <option value="CUSTOM">Customizado (em breve)</option>
                </select>
              </div>
              <div className="form-field">
                <label htmlFor={`adj-period-${plan.key}`}>
                  Periodicidade do reajuste
                </label>
                <select
                  id={`adj-period-${plan.key}`}
                  value={plan.adjustmentPeriodicity}
                  onChange={(event) =>
                    updatePlanField(
                      planIndex,
                      'adjustmentPeriodicity',
                      event.target.value
                    )
                  }
                >
                  <option value="monthly">Mensal</option>
                  <option value="anniversary">Aniversário</option>
                </select>
              </div>
              <div className="form-field">
                <label htmlFor={`adj-addon-${plan.key}`}>
                  Acréscimo ao índice (%)
                </label>
                <input
                  id={`adj-addon-${plan.key}`}
                  type="number"
                  min="0"
                  step="0.01"
                  value={plan.adjustmentAddonRate}
                  onChange={(event) =>
                    updatePlanField(
                      planIndex,
                      'adjustmentAddonRate',
                      event.target.valueAsNumber || 0
                    )
                  }
                />
              </div>
            </div>
            <div className="installments">
              <h3>Parcelas</h3>
              <div className="table-responsive">
                <table className="table editable-table">
                  <thead>
                    <tr>
                      <th>Vencimento</th>
                      <th>Valor</th>
                      <th style={{ width: '50px' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.installments.map((item, installmentIndex) => (
                      <tr key={`installment-${plan.key}-${installmentIndex}`}>
                        <td>
                          <input
                            type="date"
                            value={item.due_date}
                            onChange={(event) =>
                              updateInstallment(
                                planIndex,
                                installmentIndex,
                                'due_date',
                                event.target.value
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
                              updateInstallment(
                                planIndex,
                                installmentIndex,
                                'amount',
                                event.target.valueAsNumber || 0
                              )
                            }
                          />
                        </td>
                        <td>
                          <button
                            type="button"
                            className="remove"
                            onClick={() =>
                              removeInstallment(planIndex, installmentIndex)
                            }
                            aria-label="Remover parcela"
                            disabled={plan.installments.length === 1}
                          >
                            ×
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
            <span className="badge">
              {result.outcomes.length} combinação(ões)
            </span>
          </header>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Origem</th>
                  <th>Plano</th>
                  <th>Produto</th>
                  <th>PV (Original)</th>
                  <th>PV (Corrigido)</th>
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
