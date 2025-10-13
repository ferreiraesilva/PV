import { apiFetch } from './http';
import type {
  CommercialPlan,
  FinancialSettings,
  PaymentPlanTemplate,
  TenantPlanSubscription,
  TenantSummary,
} from './types';

const SUPERUSER_BASE = '/v1/admin-portal/superuser';
const TENANT_ADMIN_BASE = '/v1/admin-portal/tenant-admin';

type RawFinancialSettings = {
  tenant_id: string;
  periods_per_year: number | null;
  default_multiplier: number | null;
  cancellation_multiplier: number | null;
};

const mapFinancialSettings = (payload: RawFinancialSettings): FinancialSettings => ({
  tenantId: payload.tenant_id,
  periodsPerYear: payload.periods_per_year,
  defaultMultiplier: payload.default_multiplier,
  cancellationMultiplier: payload.cancellation_multiplier,
});

export interface FinancialSettingsUpdatePayload {
  periodsPerYear?: number | null;
  defaultMultiplier?: number | null;
  cancellationMultiplier?: number | null;
}

export interface PaymentPlanInstallmentInput {
  period: number;
  amount: number;
}

export interface PaymentPlanTemplateCreatePayload {
  productCode: string;
  principal: number;
  discountRate: number;
  name?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown> | null;
  isActive?: boolean;
  installments: PaymentPlanInstallmentInput[];
}

export interface PaymentPlanTemplateUpdatePayload {
  name?: string | null;
  description?: string | null;
  principal?: number;
  discountRate?: number;
  metadata?: Record<string, unknown> | null;
  isActive?: boolean;
  installments?: PaymentPlanInstallmentInput[];
}

interface RawPaymentPlanTemplate extends PaymentPlanTemplate {
  installments: Array<PaymentPlanTemplate['installments'][number]>;
}

const mapPaymentPlanTemplate = (payload: RawPaymentPlanTemplate): PaymentPlanTemplate => ({
  ...payload,
  metadata: payload.metadata ?? null,
  description: payload.description ?? null,
  name: payload.name ?? null,
  installments: payload.installments.map((item) => ({
    id: item.id,
    period: item.period,
    amount: item.amount,
  })),
});

export async function listTenants(token: string, includeInactive = false): Promise<TenantSummary[]> {
  const query = includeInactive ? '?include_inactive=true' : '';
  return apiFetch<TenantSummary[]>(`${TENANT_ADMIN_BASE}/tenants${query}`, { token });
}

export async function listCommercialPlans(token: string, includeInactive = false): Promise<CommercialPlan[]> {
  const query = includeInactive ? '?include_inactive=true' : '';
  return apiFetch<CommercialPlan[]>(`${SUPERUSER_BASE}/plans${query}`, { token });
}

export interface CommercialPlanCreatePayload {
  name: string;
  description?: string | null;
  maxUsers?: number | null;
  priceCents?: number | null;
  currency?: string;
  billingCycleMonths?: number;
}

export interface CommercialPlanUpdatePayload extends CommercialPlanCreatePayload {
  isActive?: boolean;
}

export async function updateCommercialPlan(
  token: string,
  planId: string,
  payload: CommercialPlanUpdatePayload,
): Promise<CommercialPlan> {
  return apiFetch<CommercialPlan>(`${SUPERUSER_BASE}/plans/${planId}`, {
    token,
    method: 'PATCH',
    body: payload,
  });
}

export async function createCommercialPlan(
  token: string,
  payload: CommercialPlanCreatePayload,
): Promise<CommercialPlan> {
  return apiFetch<CommercialPlan>(`${SUPERUSER_BASE}/plans`, {
    token,
    method: 'POST',
    body: payload,
  });
}

export async function assignPlanToTenant(
  token: string,
  tenantId: string,
  planId: string,
): Promise<TenantPlanSubscription> {
  return apiFetch<TenantPlanSubscription>(`${SUPERUSER_BASE}/tenants/${tenantId}/assign-plan`, {
    token,
    method: 'POST',
    body: { planId },
  });
}

export async function getFinancialSettings(token: string, tenantId: string): Promise<FinancialSettings> {
  const response = await apiFetch<RawFinancialSettings>(`${TENANT_ADMIN_BASE}/${tenantId}/financial-settings`, {
    token,
  });
  return mapFinancialSettings(response);
}

export async function updateFinancialSettings(
  token: string,
  tenantId: string,
  payload: FinancialSettingsUpdatePayload,
): Promise<FinancialSettings> {
  const body: Record<string, number | null> = {};
  if (Object.prototype.hasOwnProperty.call(payload, 'periodsPerYear')) {
    body.periods_per_year = payload.periodsPerYear ?? null;
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'defaultMultiplier')) {
    body.default_multiplier = payload.defaultMultiplier ?? null;
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'cancellationMultiplier')) {
    body.cancellation_multiplier = payload.cancellationMultiplier ?? null;
  }
  const response = await apiFetch<RawFinancialSettings>(`${TENANT_ADMIN_BASE}/${tenantId}/financial-settings`, {
    token,
    method: 'PUT',
    body,
  });
  return mapFinancialSettings(response);
}

export async function listPaymentPlanTemplates(token: string, tenantId: string): Promise<PaymentPlanTemplate[]> {
  const response = await apiFetch<RawPaymentPlanTemplate[]>(
    `${TENANT_ADMIN_BASE}/${tenantId}/payment-plans`,
    { token },
  );
  return response.map(mapPaymentPlanTemplate);
}

export async function createPaymentPlanTemplate(
  token: string,
  tenantId: string,
  payload: PaymentPlanTemplateCreatePayload,
): Promise<PaymentPlanTemplate> {
  const response = await apiFetch<RawPaymentPlanTemplate>(`${TENANT_ADMIN_BASE}/${tenantId}/payment-plans`, {
    token,
    method: 'POST',
    body: payload,
  });
  return mapPaymentPlanTemplate(response);
}

export async function updatePaymentPlanTemplate(
  token: string,
  tenantId: string,
  templateId: string,
  payload: PaymentPlanTemplateUpdatePayload,
): Promise<PaymentPlanTemplate> {
  const response = await apiFetch<RawPaymentPlanTemplate>(
    `${TENANT_ADMIN_BASE}/${tenantId}/payment-plans/${templateId}`,
    {
      token,
      method: 'PATCH',
      body: payload,
    },
  );
  return mapPaymentPlanTemplate(response);
}
