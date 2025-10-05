import { useEffect, useMemo, useState } from 'react';

import {
  attachCompanies,
  confirmPasswordReset,
  fetchCompanies,
  fetchPlans,
  fetchTenants,
  fetchUsers,
  initiatePasswordReset,
  reinstateUser,
  suspendUser,
  type AdminUserAccount,
  type CompanyCreatePayload,
  type TenantCompany,
  type TenantSummary,
  type CommercialPlan,
  type PasswordResetTokenPayload,
} from '../api/administration';
import { useAuth } from '../hooks/useAuth';
import './AdministrationPage.css';

interface ResetTokenState {
  [userId: string]: PasswordResetTokenPayload;
}

export default function AdministrationPage() {
  const { accessToken, tenantId } = useAuth();
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [plans, setPlans] = useState<CommercialPlan[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [companies, setCompanies] = useState<TenantCompany[]>([]);
  const [users, setUsers] = useState<AdminUserAccount[]>([]);
  const [passwordTokens, setPasswordTokens] = useState<ResetTokenState>({});
  const [includeInactiveUsers, setIncludeInactiveUsers] = useState(false);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveTenantId = selectedTenantId ?? tenantId ?? null;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    let cancelled = false;
    setLoadingTenants(true);
    (async () => {
      try {
        const [tenantList, planList] = await Promise.all([
          fetchTenants(accessToken, true),
          fetchPlans(accessToken, true),
        ]);
        if (cancelled) {
          return;
        }
        setTenants(tenantList);
        setPlans(planList);
        if (!selectedTenantId && tenantList.length > 0) {
          setSelectedTenantId(tenantList[0].id);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) {
          setLoadingTenants(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken || !effectiveTenantId) {
      setCompanies([]);
      setUsers([]);
      return;
    }
    let cancelled = false;
    setLoadingMembers(true);
    setError(null);
    (async () => {
      try {
        const [companyList, userList] = await Promise.all([
          fetchCompanies(accessToken, effectiveTenantId, true),
          fetchUsers(accessToken, effectiveTenantId, includeInactiveUsers),
        ]);
        if (!cancelled) {
          setCompanies(companyList);
          setUsers(userList);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) {
          setLoadingMembers(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken, effectiveTenantId, includeInactiveUsers]);

  const selectedTenant = useMemo(
    () => tenants.find((tenant) => tenant.id === effectiveTenantId) ?? null,
    [tenants, effectiveTenantId],
  );

  const handleSuspend = async (userId: string) => {
    if (!accessToken || !effectiveTenantId) {
      return;
    }
    try {
      const updated = await suspendUser(accessToken, effectiveTenantId, userId);
      setUsers((current) => current.map((user) => (user.id === updated.id ? updated : user)));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleReinstate = async (userId: string, reactivate: boolean) => {
    if (!accessToken || !effectiveTenantId) {
      return;
    }
    try {
      const updated = await reinstateUser(accessToken, effectiveTenantId, userId, reactivate);
      setUsers((current) => current.map((user) => (user.id === updated.id ? updated : user)));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleInitiateReset = async (userId: string) => {
    if (!accessToken || !effectiveTenantId) {
      return;
    }
    try {
      const token = await initiatePasswordReset(accessToken, effectiveTenantId, userId);
      setPasswordTokens((current) => ({ ...current, [userId]: token }));
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleConfirmReset = async (userId: string) => {
    if (!accessToken || !effectiveTenantId) {
      return;
    }
    const currentToken = passwordTokens[userId]?.token ?? '';
    const resetToken = window.prompt('Informe o token de reset distribuído ao usuário', currentToken);
    if (!resetToken) {
      return;
    }
    const newPassword = window.prompt('Informe a nova senha temporária para o usuário');
    if (!newPassword) {
      return;
    }
    try {
      const updated = await confirmPasswordReset(accessToken, effectiveTenantId, userId, resetToken, newPassword);
      setUsers((current) => current.map((user) => (user.id === updated.id ? updated : user)));
      setPasswordTokens((current) => {
        const { [userId]: _discard, ...rest } = current;
        return rest;
      });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleAttachCompany = async (payload: CompanyCreatePayload) => {
    if (!accessToken || !effectiveTenantId) {
      return;
    }
    try {
      const [created] = await attachCompanies(accessToken, effectiveTenantId, [payload]);
      if (created) {
        setCompanies((current) => [...current, created]);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="administration-page">
      <header className="administration-header">
        <div>
          <h1>Administração de Tenants</h1>
          <p>Gerencie planos, empresas e contas administrativas.</p>
        </div>
        <div className="filters">
          <label>
            Tenant
            <select
              value={effectiveTenantId ?? ''}
              onChange={(event) => setSelectedTenantId(event.target.value || null)}
              disabled={loadingTenants || tenants.length === 0}
            >
              {tenants.map((tenantOption) => (
                <option key={tenantOption.id} value={tenantOption.id}>
                  {tenantOption.name} {tenantOption.isDefault ? '(default)' : ''}
                </option>
              ))}
            </select>
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={includeInactiveUsers}
              onChange={(event) => setIncludeInactiveUsers(event.target.checked)}
            />
            Mostrar usuários inativos
          </label>
        </div>
      </header>

      {error && <div className="alert error">{error}</div>}

      <section className="plans-section">
        <h2>Planos comerciais</h2>
        {plans.length === 0 ? (
          <p className="muted">Nenhum plano cadastrado.</p>
        ) : (
          <ul className="plan-list">
            {plans.map((plan) => (
              <li key={plan.id} className={!plan.isActive ? 'inactive' : undefined}>
                <div>
                  <strong>{plan.name}</strong>
                  {plan.description && <span className="muted"> — {plan.description}</span>}
                </div>
                <div className="details">
                  <span>Usuários: {plan.maxUsers ?? 'ilimitado'}</span>
                  <span>Ciclo: {plan.billingCycleMonths} mês(es)</span>
                  <span>Status: {plan.isActive ? 'Ativo' : 'Inativo'}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="two-column">
        <div>
          <h2>Empresas vinculadas</h2>
          {loadingMembers ? (
            <p className="muted">Carregando empresas…</p>
          ) : companies.length === 0 ? (
            <p className="muted">Nenhuma empresa cadastrada.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Razão social</th>
                  <th>CNPJ/ID fiscal</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={company.id}>
                    <td>{company.legalName}</td>
                    <td>{company.taxId}</td>
                    <td>{company.isActive ? 'Ativa' : 'Inativa'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <button
            type="button"
            className="secondary"
            onClick={() =>
              handleAttachCompany({
                legalName: 'Nova Empresa',
                taxId: Date.now().toString(),
                billingEmail: 'finance@example.com',
                addressLine1: 'Rua Exemplo, 123',
                city: 'Sao Paulo',
                state: 'SP',
                zipCode: '01000-000',
              })
            }
            disabled={!effectiveTenantId}
          >
            Adicionar empresa de teste
          </button>
        </div>
        <div>
          <h2>Usuários administrativos</h2>
          {loadingMembers ? (
            <p className="muted">Carregando usuários…</p>
          ) : users.length === 0 ? (
            <p className="muted">Nenhum usuário encontrado.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>E-mail</th>
                  <th>Nome</th>
                  <th>Perfis</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => {
                  const resetInfo = passwordTokens[user.id];
                  return (
                    <tr key={user.id}>
                      <td>{user.email}</td>
                      <td>{user.fullName ?? '—'}</td>
                      <td>{user.roles.join(', ') || '—'}</td>
                      <td>
                        {user.isActive ? 'Ativo' : 'Inativo'}
                        {user.isSuspended ? ' • Suspenso' : ''}
                      </td>
                      <td className="actions">
                        {user.isSuspended ? (
                          <button type="button" onClick={() => handleReinstate(user.id, true)}>
                            Reativar
                          </button>
                        ) : (
                          <button type="button" onClick={() => handleSuspend(user.id)}>
                            Suspender
                          </button>
                        )}
                        <button type="button" onClick={() => handleInitiateReset(user.id)}>
                          Gerar token de reset
                        </button>
                        <button type="button" onClick={() => handleConfirmReset(user.id)}>
                          Aplicar nova senha
                        </button>
                        {resetInfo && (
                          <span className="reset-token">
                            Token: <code>{resetInfo.token}</code>
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
