import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { useBenchmarking } from '../hooks/useBenchmarking';
import './BenchmarkingPage.css';

export default function BenchmarkingPage() {
  const { tenantId } = useAuth();
  const {
    batchId,
    setBatchId,
    aggregation,
    error,
    loading,
    fetching,
    handleFileChange,
    handleIngest,
    fetchAggregations,
  } = useBenchmarking();

  if (!tenantId) {
    return (
      <div className="card">
        <p>Autentique-se para acessar as rotinas de benchmarking.</p>
      </div>
    );
  }

  return (
    <div className="stack">
      <PageHeader
        title="Benchmarking de mercado"
        subtitle="Carregue datasets anonimizados para gerar métricas agregadas por segmento e região."
        actions={
          <button className="button ghost" type="button" onClick={fetchAggregations} disabled={fetching}>
            {fetching ? 'Buscando...' : 'Atualizar agregações'}
          </button>
        }
      />
      <form className="card stack" onSubmit={handleIngest}>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="batchId">Batch ID</label>
            <input
              id="batchId"
              value={batchId}
              onChange={(event) => setBatchId(event.target.value)}
              placeholder="UUID do lote"
            />
            <small>Use o UUID que identifica o lote de benchmarking.</small>
          </div>
          <div className="form-field">
            <label htmlFor="dataset">Arquivo benchmarking</label>
            <input id="dataset" type="file" accept=".csv,.xlsx" onChange={handleFileChange} />
            <small>A planilha deve conter colunas metric_code, segment, region, value.</small>
          </div>
        </div>
        {error && <div className="alert error">{error}</div>}
        <button className="button" type="submit" disabled={loading}>
          {loading ? 'Processando...' : 'Enviar dataset'}
        </button>
      </form>
      {aggregation && (
        <section className="card stack">
          <header className="aggregation-header">
            <div>
              <h2>Agregações do lote</h2>
              <p>Resumo calculado pelo backend para garantir anonimização (k ≥ 3).</p>
            </div>
            <div className="aggregation-stats">
              {typeof aggregation.totalRows === 'number' && (
                <div>
                  <span className="label">Linhas processadas</span>
                  <p className="value">{aggregation.totalRows}</p>
                </div>
              )}
              {typeof aggregation.discardedRows === 'number' && (
                <div>
                  <span className="label">Descartadas</span>
                  <p className="value">{aggregation.discardedRows}</p>
                </div>
              )}
            </div>
          </header>
          {aggregation.rows.length === 0 ? (
            <p>Nenhum bucket elegível encontrado para o lote informado.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Métrica</th>
                  <th>Segmento</th>
                  <th>Região</th>
                  <th>Qtd.</th>
                  <th>Média</th>
                  <th>Mínimo</th>
                  <th>Máximo</th>
                </tr>
              </thead>
              <tbody>
                {aggregation.rows.map((row, index) => (
                  <tr key={`${row.metricCode}-${row.segmentBucket}-${row.regionBucket}-${index}`}>
                    <td>{row.metricCode}</td>
                    <td>{row.segmentBucket}</td>
                    <td>{row.regionBucket}</td>
                    <td>{row.count}</td>
                    <td>{row.averageValue.toLocaleString('pt-BR')}</td>
                    <td>{row.minValue.toLocaleString('pt-BR')}</td>
                    <td>{row.maxValue.toLocaleString('pt-BR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}