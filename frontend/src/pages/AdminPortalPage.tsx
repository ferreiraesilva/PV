import { useEffect, useMemo, useState } from 'react';

import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { SuperuserPanel } from '../components/SuperuserPanel';
import { TenantAdminPanel } from '../components/TenantAdminPanel';
import { listTenants } from '../api/adminPortal';
import type { TenantSummary } from '../api/types';
import './AdminPortalPage.css';

type ActiveTab = 'tenant' | 'superuser';

const AdminPortalPage = () => {
  const { accessToken, tenantId, roles } = useAuth();
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [tenantsLoading, setTenantsLoading] = useState(false);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(
    tenantId ?? null
  );
  const [activeTab, setActiveTab] = useState<ActiveTab>(
    roles.includes('superadmin') ? 'superuser' : 'tenant'
  );
  const [error, setError] = useState<string | null>(null);

  const isSuperuser = roles.includes('superadmin');
  const isTenantAdmin = roles.includes('tenant_admin') || isSuperuser;

  useEffect(() => {
    if (!accessToken || !isTenantAdmin) {
      return;
    }
    let cancelled = false;
    setTenantsLoading(true);
    setError(null);
    (async () => {
      try {
        const data = await listTenants(accessToken, true);
        if (!cancelled) {
          setTenants(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) {
          setTenantsLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken, isTenantAdmin]);

  useEffect(() => {
    if (!tenantId) {
      return;
    }
    setSelectedTenantId((current) => current ?? tenantId);
  }, [tenantId]);

  useEffect(() => {
    if (!selectedTenantId && tenants.length > 0) {
      setSelectedTenantId(tenants[0].id);
    }
  }, [tenants, selectedTenantId]);

  useEffect(() => {
    setActiveTab(isSuperuser ? 'superuser' : 'tenant');
  }, [isSuperuser]);

  const canShowSuperuserTab = isSuperuser;
  const canShowTenantTab = isTenantAdmin;

  const tenantOptions = useMemo(
    () => [...tenants].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')),
    [tenants]
  );

  return (
    <div className="admin-portal-page stack">
      <PageHeader
        title="Portal Administrativo"
        subtitle="Gerencie planos, tenants e parâmetros financeiros em um único lugar."
      />

      {(error || tenantsLoading) && (
        <div className={error ? 'alert error' : 'alert'}>
          {error ?? 'Carregando informações dos tenants...'}
        </div>
      )}

      <div className="portal-tabs">
        {canShowSuperuserTab && (
          <button
            type="button"
            className={`portal-tab${activeTab === 'superuser' ? ' active' : ''}`}
            onClick={() => setActiveTab('superuser')}
          >
            Superusuário
          </button>
        )}
        {canShowTenantTab && (
          <button
            type="button"
            className={`portal-tab${activeTab === 'tenant' ? ' active' : ''}`}
            onClick={() => setActiveTab('tenant')}
          >
            Tenant admin
          </button>
        )}
      </div>

      <div className="portal-content">
        {canShowSuperuserTab && activeTab === 'superuser' && (
          <SuperuserPanel accessToken={accessToken} tenants={tenantOptions} />
        )}
        {canShowTenantTab && activeTab === 'tenant' && (
          <TenantAdminPanel
            accessToken={accessToken}
            tenants={tenantOptions}
            selectedTenantId={selectedTenantId}
            onSelectTenant={setSelectedTenantId}
            canSelectTenant={isSuperuser}
          />
        )}
      </div>
    </div>
  );
};

export default AdminPortalPage;
