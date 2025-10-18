import { NavLink, Outlet } from "react-router-dom";
import type { ReactNode } from "react";

import { useAuth } from "../hooks/useAuth";
import "./AppLayout.css";

const BASE_NAV_ITEMS = [
  { to: "/", label: "Visao geral" },
  { to: "/simulations", label: "Simulacoes" },
  { to: "/valuations", label: "Valuation" },
  { to: "/benchmarking", label: "Benchmarking" },
  { to: "/recommendations", label: "Recomendacoes" },
  { to: "/audit", label: "Auditoria" },
];

interface AppLayoutProps {
  onLogout: () => Promise<void> | void;
  children?: ReactNode;
}

export function AppLayout({ onLogout, children }: AppLayoutProps) {
  const { tenantId, roles } = useAuth();

  const isSuperuser = roles.includes("superadmin");
  const isTenantAdmin = isSuperuser || roles.includes("tenant_admin");

  const navItems = [...BASE_NAV_ITEMS];

  if (isTenantAdmin) {
    navItems.push({ to: "/indexes", label: "Indices" });
    navItems.push({ to: "/admin", label: "Administracao" });
  }

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
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
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
