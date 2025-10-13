import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { useAudit } from '../hooks/useAudit';
import type { AuditLogEntry } from '../api/types';
import './AuditPage.css';

export default function AuditPage() {
  const { tenantId } = useAuth();
  const {
    filters,
    logs,
    error,
    loading,
    page,
    hasNextPage,
    sortBy,
    sortOrder,
    handleFilterChange,
    setPage,
    handleSubmit,
    handleClear,
    handleSort,
  } = useAudit();

  const SortableHeader = ({
    column,
    label,
  }: {
    column: keyof AuditLogEntry;
    label: string;
  }) => {
    const isSorted = sortBy === column;
    const icon = isSorted ? (sortOrder === 'asc' ? '▲' : '▼') : '';
    return (
      <th onClick={() => handleSort(column)} className="sortable">
        {label} {icon}
      </th>
    );
  };

  if (!tenantId) {
    return (
      <div className="card">
        <p>Realize login para visualizar logs de auditoria.</p>
      </div>
    );
  }

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
              onChange={(event) =>
                handleFilterChange('from', event.target.value)
              }
            />
          </div>
          <div className="form-field">
            <label htmlFor="to">Até</label>
            <input
              id="to"
              type="datetime-local"
              value={filters.to}
              onChange={(event) => handleFilterChange('to', event.target.value)}
            />
          </div>
        </div>
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="requestId">Request ID</label>
            <input
              id="requestId"
              value={filters.requestId}
              onChange={(event) =>
                handleFilterChange('requestId', event.target.value)
              }
              placeholder="UUID do request"
            />
          </div>
          <div className="form-field">
            <label htmlFor="userId">Usuário</label>
            <input
              id="userId"
              value={filters.userId}
              onChange={(event) =>
                handleFilterChange('userId', event.target.value)
              }
              placeholder="UUID do usuário"
            />
          </div>
        </div>
        {error && <div className="alert error">{error}</div>}
        <div className="actions">
          <button className="button ghost" type="button" onClick={handleClear}>
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
          <p>{logs.length > 0 ? `Exibindo ${logs.length} registros.` : ''}</p>
        </header>
        {logs.length === 0 ? (
          <p>Nenhum log encontrado para os filtros aplicados.</p>
        ) : (
          <div className="audit-table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <SortableHeader column="id" label="ID" />
                  <SortableHeader column="occurredAt" label="Data" />
                  <SortableHeader column="requestId" label="Request" />
                  <SortableHeader column="userId" label="User" />
                  <SortableHeader column="method" label="Método" />
                  <SortableHeader column="endpoint" label="Endpoint" />
                  <SortableHeader column="statusCode" label="Status" />
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
        {(page > 1 || hasNextPage) && (
          <footer className="pagination-footer">
            <span>Página {page}</span>
            <div className="pagination-controls">
              <button
                className="button ghost"
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 1 || loading}
              >
                Anterior
              </button>
              <button
                className="button ghost"
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasNextPage || loading}
              >
                Próxima
              </button>
            </div>
          </footer>
        )}
      </section>
    </div>
  );
}
