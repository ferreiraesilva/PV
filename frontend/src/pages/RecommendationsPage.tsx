import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { useRecommendations } from '../hooks/useRecommendations';
import './RecommendationsPage.css';

export default function RecommendationsPage() {
  const { tenantId } = useAuth();
  const {
    runType,
    setRunType,
    snapshotId,
    setSnapshotId,
    simulationId,
    setSimulationId,
    parameters,
    setParameters,
    jobStatus,
    runDetail,
    runId,
    setRunId,
    error,
    loading,
    fetching,
    handleStartRun,
    handleFetchRun,
  } = useRecommendations();

  if (!tenantId) {
    return (
      <div className="card">
        <p>FaÃ§a login para acessar recomendações.</p>
      </div>
    );
  }

  return (
    <div className="stack">
      <PageHeader
        title="RecomendaÃ§Ãµes (IA)"
        subtitle="Orquestre execuÃ§Ãµes de modelos preditivos e acompanhe status dos runs."
        actions={
          <button
            className="button ghost"
            type="button"
            onClick={handleFetchRun}
            disabled={fetching}
          >
            {fetching ? 'Consultando...' : 'Consultar run'}
          </button>
        }
      />
      <form className="card stack" onSubmit={handleStartRun}>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="runType">Tipo do run</label>
            <input
              id="runType"
              value={runType}
              onChange={(event) => setRunType(event.target.value)}
            />
            <small>Ex.: pricing, churn, clusterizaÃ§Ã£o.</small>
          </div>
          <div className="form-field">
            <label htmlFor="runId">Run ID</label>
            <input
              id="runId"
              value={runId}
              onChange={(event) => setRunId(event.target.value)}
              placeholder="jobId retornado no start"
            />
            <small>
              Use este identificador para consultar o run posteriormente.
            </small>
          </div>
        </div>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="snapshotId">Snapshot ID (opcional)</label>
            <input
              id="snapshotId"
              value={snapshotId}
              onChange={(event) => setSnapshotId(event.target.value)}
              placeholder="UUID do snapshot"
            />
          </div>
          <div className="form-field">
            <label htmlFor="simulationId">Simulation ID (opcional)</label>
            <input
              id="simulationId"
              value={simulationId}
              onChange={(event) => setSimulationId(event.target.value)}
              placeholder="UUID da simulaÃ§Ã£o"
            />
          </div>
        </div>
        <div className="form-field">
          <label htmlFor="parameters">ParÃ¢metros adicionais (JSON)</label>
          <textarea
            id="parameters"
            value={parameters}
            rows={5}
            onChange={(event) => setParameters(event.target.value)}
          />
        </div>
        {error && <div className="alert error">{error}</div>}
        <button className="button" type="submit" disabled={loading}>
          {loading ? 'Enviando...' : 'Iniciar run de recomendaÃ§Ãµes'}
        </button>
      </form>
      {jobStatus && (
        <section className="card">
          <h2>Status do job</h2>
          <div className="grid two">
            <div>
              <span className="label">jobId</span>
              <p className="value">{jobStatus.jobId}</p>
            </div>
            <div>
              <span className="label">Status</span>
              <p className="value">{jobStatus.status}</p>
            </div>
            <div>
              <span className="label">Enviado em</span>
              <p className="value">
                {new Date(jobStatus.submittedAt).toLocaleString()}
              </p>
            </div>
            <div>
              <span className="label">Finalizado em</span>
              <p className="value">
                {jobStatus.completedAt
                  ? new Date(jobStatus.completedAt).toLocaleString()
                  : 'â€”'}
              </p>
            </div>
          </div>
          {jobStatus.message && (
            <div className="alert">{jobStatus.message}</div>
          )}
        </section>
      )}
      {runDetail && (
        <section className="card stack">
          <header>
            <h2>Detalhes do run</h2>
            <p>Status atual e itens recomendados pelo backend.</p>
          </header>
          <div className="grid two">
            <div>
              <span className="label">Run type</span>
              <p className="value">{runDetail.runType}</p>
            </div>
            <div>
              <span className="label">Status</span>
              <p className="value">{runDetail.status}</p>
            </div>
          </div>
          {runDetail.items.length === 0 ? (
            <p>Nenhuma recomendaÃ§Ã£o foi retornada.</p>
          ) : (
            <ul className="recommendations-list">
              {runDetail.items.map((item, index) => (
                <li key={`${item.title}-${index}`}>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                  <span className="badge">Prioridade: {item.priority}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
