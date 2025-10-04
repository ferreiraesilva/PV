import { NavLink, Outlet } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth } from '../hooks/useAuth';
import './AppLayout.css';

const NAV_ITEMS = [
  { to: '/', label: 'Visão geral', exact: true },
  { to: '/simulations', label: 'Simulações' },
  { to: '/valuations', label: 'Valuation' },
  { to: '/benchmarking', label: 'Benchmarking' },
  { to: '/recommendations', label: 'Recomendações' },
  { to: '/audit', label: 'Auditoria' },
];

interface AppLayoutProps {
  onLogout: () => Promise<void> | void;
  children?: ReactNode;
}

export function AppLayout({ onLogout, children }: AppLayoutProps) {
  const { tenantId } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <strong>SAFV Console</strong>
        </div>
        <div className="header-actions">
          {tenantId && <span className="tenant-pill">Tenant: {tenantId}</span>}
          <button type="button" className="secondary" onClick={() => onLogout()}>
            Sair
          </button>
        </div>
      </header>
      <div className="app-body">
        <aside className="sidebar" aria-label="Menu principal">
          <nav>
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="app-content">{children ?? <Outlet />}</main>
      </div>
    </div>
  );
}
