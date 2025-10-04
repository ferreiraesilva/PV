import { FormEvent, useState } from 'react';

import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { listAuditLogs } from '../api/audit';
import type { AuditLogEntry } from '../api/types';
import './AuditPage.css';

interface AuditFiltersState {
  from: string;
  to: string;
  requestId: string;
  userId: string;
}

const DEFAULT_FILTERS: AuditFiltersState = {
  from: '',
  to: '',
  requestId: '',
  userId: '',
};

export default function AuditPage() {
  const { tenantId, accessToken } = useAuth();
  const [filters, setFilters] = useState<AuditFiltersState>(DEFAULT_FILTERS);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Realize login para visualizar logs de auditoria.</p>
      </div>
    );
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      setLoading(true);
      const cleanFilters = {
        from: filters.from ? new Date(filters.from).toISOString() : undefined,
        to: filters.to ? new Date(filters.to).toISOString() : undefined,
        requestId: filters.requestId || undefined,
        userId: filters.userId || undefined,
      };
      const response = await listAuditLogs(tenantId, accessToken, cleanFilters);
      setLogs(response);
    } catch (err) {
      const message = (err as Error).message ?? 'Erro ao consultar auditoria (endpoint pode não estar publicado).';
      setError(message);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stack">
      <PageHeader
        title="Auditoria"
        subtitle="Pesquise logs imutáveis por intervalo de datas, requestId ou usuário."
      />
      <form className="card filters" onSubmit={handleSubmit}>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="from">De</label>
            <input
              id="from"
              type="datetime-local"
              value={filters.from}
              onChange={(event) => setFilters((current) => ({ ...current, from: event.target.value }))}
            />
          </div>
          <div className="form-field">
            <label htmlFor="to">Até</label>
            <input
              id="to"
              type="datetime-local"
              value={filters.to}
              onChange={(event) => setFilters((current) => ({ ...current, to: event.target.value }))}
            />
          </div>
        </div>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="requestId">Request ID</label>
            <input
              id="requestId"
              value={filters.requestId}
              onChange={(event) => setFilters((current) => ({ ...current, requestId: event.target.value }))}
              placeholder="UUID do request"
            />
          </div>
          <div className="form-field">
            <label htmlFor="userId">Usuário</label>
            <input
              id="userId"
              value={filters.userId}
              onChange={(event) => setFilters((current) => ({ ...current, userId: event.target.value }))}
              placeholder="UUID do usuário"
            />
          </div>
        </div>
        {error && <div className="alert error">{error}</div>}
        <div className="actions">
          <button className="button ghost" type="button" onClick={() => setFilters(DEFAULT_FILTERS)}>
            Limpar filtros
          </button>
          <button className="button" type="submit" disabled={loading}>
            {loading ? 'Consultando...' : 'Buscar logs'}
          </button>
        </div>
      </form>
      <section className="card audit-results">
        <header>
          <h2>Resultados</h2>
          <p>{logs.length} registros retornados.</p>
        </header>
        {logs.length === 0 ? (
          <p>Nenhum log encontrado para os filtros aplicados.</p>
        ) : (
          <div className="audit-table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Data</th>
                  <th>Request</th>
                  <th>User</th>
                  <th>Método</th>
                  <th>Endpoint</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{new Date(log.occurredAt).toLocaleString()}</td>
                    <td>{log.requestId}</td>
                    <td>{log.userId ?? '—'}</td>
                    <td>{log.method}</td>
                    <td>{log.endpoint}</td>
                    <td>{log.statusCode}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
