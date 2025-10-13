import { useEffect, useMemo, useState } from 'react';

import type { CommercialPlan, TenantSummary } from '../api/types';
import {
  assignPlanToTenant,
  createCommercialPlan,
  listCommercialPlans,
  updateCommercialPlan,
  type CommercialPlanCreatePayload,
  type CommercialPlanUpdatePayload,
} from '../api/adminPortal';

interface SuperuserPanelProps {
  accessToken: string | null;
  tenants: TenantSummary[];
}

interface PlanDraft {
  id?: string;
  name: string;
  description: string;
  maxUsers: string;
  price: string;
  currency: string;
  billingCycleMonths: string;
  isActive: boolean;
}

const defaultPlanDraft = (): PlanDraft => ({
  name: '',
  description: '',
  maxUsers: '',
  price: '',
  currency: 'BRL',
  billingCycleMonths: '1',
  isActive: true,
});

const planToDraft = (plan: CommercialPlan): PlanDraft => ({
  id: plan.id,
  name: plan.name,
  description: plan.description ?? '',
  maxUsers: plan.maxUsers?.toString() ?? '',
  price: plan.priceCents ? (plan.priceCents / 100).toString() : '',
  currency: plan.currency,
  billingCycleMonths: plan.billingCycleMonths.toString(),
  isActive: plan.isActive,
});

const parseOptionalInteger = (value: string, field: string): number | null => {
  if (value.trim() === '') {
    return null;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || !Number.isInteger(parsed)) {
    throw new Error(`Informe um número inteiro válido em "${field}".`);
  }
  return parsed;
};

const parseRequiredInteger = (value: string, field: string): number => {
  const parsed = parseOptionalInteger(value, field);
  if (parsed === null || parsed <= 0) {
    throw new Error(`O campo "${field}" deve ser um inteiro positivo.`);
  }
  return parsed;
};

const parsePriceCents = (value: string): number | null => {
  if (value.trim() === '') {
    return null;
  }
  const parsed = Number(value.replace(',', '.'));
  if (!Number.isFinite(parsed)) {
    throw new Error('Informe um valor numérico para o preço.');
  }
  return Math.round(parsed * 100);
};

export function SuperuserPanel({ accessToken, tenants }: SuperuserPanelProps) {
  const [plans, setPlans] = useState<CommercialPlan[]>([]);
  const [plansLoading, setPlansLoading] = useState(false);
  const [planDraft, setPlanDraft] = useState<PlanDraft | null>(null);
  const [planSaving, setPlanSaving] = useState(false);
  const [planStatus, setPlanStatus] = useState<string | null>(null);

  const [assignTenantId, setAssignTenantId] = useState<string>('');
  const [assignPlanId, setAssignPlanId] = useState<string>('');
  const [assignLoading, setAssignLoading] = useState(false);
  const [assignStatus, setAssignStatus] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      setPlans([]);
      setPlanDraft(null);
      return;
    }
    let cancelled = false;
    setPlansLoading(true);
    setError(null);
    (async () => {
      try {
        const data = await listCommercialPlans(accessToken, true);
        if (!cancelled) {
          setPlans(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) {
          setPlansLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const sortedTenants = useMemo(
    () => [...tenants].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')),
    [tenants],
  );

  const sortedPlans = useMemo(
    () => [...plans].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')),
    [plans],
  );

  const handleStartPlanCreation = () => {
    setPlanDraft(defaultPlanDraft());
    setPlanStatus(null);
    setError(null);
  };

  const handleEditPlan = (plan: CommercialPlan) => {
    setPlanDraft(planToDraft(plan));
    setPlanStatus(null);
    setError(null);
  };

  const handlePlanChange = (field: keyof PlanDraft, value: string | boolean) => {
    if (!planDraft) {
      return;
    }
    setPlanDraft({ ...planDraft, [field]: value });
  };

  const handleCancelPlan = () => {
    setPlanDraft(null);
    setPlanStatus(null);
  };

  const buildPlanPayload = (draft: PlanDraft): CommercialPlanCreatePayload => {
    if (!draft.name.trim()) {
      throw new Error('Informe o nome do plano.');
    }
    const currency = draft.currency.trim() || 'BRL';
    const billingCycleMonths = parseRequiredInteger(draft.billingCycleMonths, 'Ciclo de cobrança');
    const maxUsers = parseOptionalInteger(draft.maxUsers, 'Usuários máximos');
    if (maxUsers !== null && maxUsers < 0) {
      throw new Error('Usuários máximos deve ser positivo.');
    }
    const priceCents = parsePriceCents(draft.price);
    if (priceCents !== null && priceCents < 0) {
      throw new Error('O preço em centavos deve ser positivo.');
    }
    return {
      name: draft.name.trim(),
      description: draft.description.trim() || null,
      maxUsers,
      priceCents,
      currency,
      billingCycleMonths,
    };
  };

  const handleSavePlan = async () => {
    if (!accessToken || !planDraft) {
      return;
    }
    setPlanSaving(true);
    setError(null);
    setPlanStatus(null);
    try {
      const basePayload = buildPlanPayload(planDraft);
      if (!planDraft.id) {
        const created = await createCommercialPlan(accessToken, basePayload);
        setPlans((current) => [...current, created]);
        setPlanDraft(planToDraft(created));
        setPlanStatus('Plano criado com sucesso.');
      } else {
        const payload: CommercialPlanUpdatePayload = {
          ...basePayload,
          isActive: planDraft.isActive,
        };
        const updated = await updateCommercialPlan(accessToken, planDraft.id, payload);
        setPlans((current) => current.map((plan) => (plan.id === updated.id ? updated : plan)));
        setPlanDraft(planToDraft(updated));
        setPlanStatus('Plano atualizado com sucesso.');
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPlanSaving(false);
    }
  };

  const handleAssignPlan = async () => {
    if (!accessToken || !assignTenantId || !assignPlanId) {
      return;
    }
    setAssignLoading(true);
    setAssignStatus(null);
    setError(null);
    try {
      await assignPlanToTenant(accessToken, assignTenantId, assignPlanId);
      const tenantName = tenants.find((tenant) => tenant.id === assignTenantId)?.name ?? assignTenantId;
      const planName = plans.find((plan) => plan.id === assignPlanId)?.name ?? assignPlanId;
      setAssignStatus(`Plano "${planName}" atribuído ao tenant "${tenantName}".`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setAssignLoading(false);
    }
  };

  return (
    <div className="stack">
      {error && (
        <div className="alert error">
          {error}
        </div>
      )}

      <section className="card stack">
        <div className="stack">
          <h2>Planos comerciais</h2>
          <div>
            <button type="button" className="button ghost" onClick={handleStartPlanCreation}>
              Novo plano
            </button>
          </div>
          {planStatus && <small>{planStatus}</small>}
        </div>

        {plansLoading ? (
          <p>Carregando planos...</p>
        ) : plans.length === 0 ? (
          <p>Nenhum plano cadastrado.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Preço</th>
                <th>Usuários</th>
                <th>Ciclo (meses)</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {sortedPlans.map((plan) => (
                <tr key={plan.id}>
                  <td>{plan.name}</td>
                  <td>
                    {plan.priceCents
                      ? (plan.priceCents / 100).toLocaleString('pt-BR', {
                        style: 'currency',
                        currency: plan.currency || 'BRL',
                      })
                      : '—'}
                  </td>
                  <td>{plan.maxUsers ?? 'Ilimitado'}</td>
                  <td>{plan.billingCycleMonths}</td>
                  <td>
                    <span className="badge">{plan.isActive ? 'Ativo' : 'Inativo'}</span>
                  </td>
                  <td>
                    <button type="button" className="button ghost" onClick={() => handleEditPlan(plan)}>
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {planDraft && (
          <div className="card stack">
            <h3>{planDraft.id ? 'Editar plano' : 'Novo plano'}</h3>
            <div className="grid two">
              <div className="form-field">
                <label htmlFor="plan-name">Nome</label>
                <input
                  id="plan-name"
                  value={planDraft.name}
                  onChange={(event) => handlePlanChange('name', event.target.value)}
                />
              </div>
              <div className="form-field">
                <label htmlFor="plan-currency">Moeda</label>
                <input
                  id="plan-currency"
                  value={planDraft.currency}
                  onChange={(event) => handlePlanChange('currency', event.target.value)}
                  placeholder="Ex: BRL"
                />
              </div>
              <div className="form-field">
                <label htmlFor="plan-price">Preço (em reais)</label>
                <input
                  id="plan-price"
                  value={planDraft.price}
                  onChange={(event) => handlePlanChange('price', event.target.value)}
                  placeholder="Ex: 199.90"
                />
              </div>
              <div className="form-field">
                <label htmlFor="plan-max-users">Usuários máximos</label>
                <input
                  id="plan-max-users"
                  value={planDraft.maxUsers}
                  onChange={(event) => handlePlanChange('maxUsers', event.target.value)}
                  placeholder="Deixe vazio para ilimitado"
                />
              </div>
              <div className="form-field">
                <label htmlFor="plan-cycle">Ciclo (meses)</label>
                <input
                  id="plan-cycle"
                  value={planDraft.billingCycleMonths}
                  onChange={(event) => handlePlanChange('billingCycleMonths', event.target.value)}
                  placeholder="Ex: 12"
                />
              </div>
            </div>

            <div className="form-field">
              <label htmlFor="plan-description">Descrição</label>
              <textarea
                id="plan-description"
                rows={3}
                value={planDraft.description}
                onChange={(event) => handlePlanChange('description', event.target.value)}
              />
            </div>

            {planDraft.id && (
              <label>
                <input
                  type="checkbox"
                  checked={planDraft.isActive}
                  onChange={(event) => handlePlanChange('isActive', event.target.checked)}
                />
                &nbsp;Plano ativo
              </label>
            )}

            <div className="grid two">
              <button
                type="button"
                className="button"
                onClick={handleSavePlan}
                disabled={planSaving}
              >
                {planSaving ? 'Salvando...' : 'Salvar plano'}
              </button>
              <button type="button" className="button ghost" onClick={handleCancelPlan}>
                Cancelar
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="card stack">
        <h2>Atribuir plano a tenant</h2>
        {assignStatus && <small>{assignStatus}</small>}
        <div className="grid two">
          <div className="form-field">
            <label htmlFor="assign-tenant">Tenant</label>
            <select
              id="assign-tenant"
              value={assignTenantId}
              onChange={(event) => setAssignTenantId(event.target.value)}
            >
              <option value="">Selecione um tenant</option>
              {sortedTenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name} {tenant.isActive ? '' : '(inativo)'}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="assign-plan">Plano</label>
            <select
              id="assign-plan"
              value={assignPlanId}
              onChange={(event) => setAssignPlanId(event.target.value)}
            >
              <option value="">Selecione um plano</option>
              {sortedPlans.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name} {plan.isActive ? '' : '(inativo)'}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="button"
          className="button"
          onClick={handleAssignPlan}
          disabled={assignLoading || !assignPlanId || !assignTenantId}
        >
          {assignLoading ? 'Aplicando...' : 'Atribuir plano'}
        </button>
      </section>
    </div>
  );
}
