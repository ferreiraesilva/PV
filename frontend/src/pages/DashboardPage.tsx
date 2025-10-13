import { NavLink } from 'react-router-dom';

import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import './DashboardPage.css';

const ACTIONS = [
  {
    title: 'Simulações financeiras',
    description:
      'Compare planos de pagamento e visualize métricas de PV, PMT e FV com poucos cliques.',
    to: '/simulations',
  },
  {
    title: 'Valuation de carteira',
    description:
      'Projete múltiplos cenários de risco com base nas probabilidades de default e cancelamento.',
    to: '/valuations',
  },
  {
    title: 'Benchmarking',
    description:
      'Carregue datasets anonimizados e gere comparativos agregados por segmento e região.',
    to: '/benchmarking',
  },
  {
    title: 'Recomendações',
    description:
      'Orquestre execuções de IA (placeholder) e acompanhe status de job e outputs gerados pelo backend.',
    to: '/recommendations',
  },
  {
    title: 'Auditoria',
    description:
      'Pesquise logs imutáveis para investigar ações por request, usuário e recurso.',
    to: '/audit',
  },
];

export default function DashboardPage() {
  const { tenantId } = useAuth();

  return (
    <div className="stack">
      <PageHeader
        title="Painel do SAFV"
        subtitle="Centralize simulações, valuations, benchmarking e auditoria em um único console."
      />
      <section className="card overview-card">
        <h2>Contexto do tenant</h2>
        <div className="grid three">
          <div>
            <span className="label">Tenant ativo</span>
            <p className="value">{tenantId ?? '—'}</p>
          </div>
          <div>
            <span className="label">Autenticação</span>
            <p className="value">
              Token JWT armazenado com refresh automático.
            </p>
          </div>
          <div>
            <span className="label">Ambiente API</span>
            <p className="value">
              {import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/v1'}
            </p>
          </div>
        </div>
      </section>
      <section className="grid two">
        {ACTIONS.map((action) => (
          <article key={action.title} className="card action-card">
            <header>
              <h3>{action.title}</h3>
              <p>{action.description}</p>
            </header>
            <NavLink to={action.to} className="button ghost">
              Abrir módulo
            </NavLink>
          </article>
        ))}
      </section>
    </div>
  );
}
