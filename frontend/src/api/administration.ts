import { apiFetch } from './http';
import {
  AdminUserAccount,
  CommercialPlan,
  PasswordResetTokenPayload,
  TenantCompany,
  TenantSummary,
} from './types';

export interface CompanyCreatePayload {
  legalName: string;
  taxId: string;
  billingEmail: string;
  addressLine1: string;
  city: string;
  state: string;
  zipCode: string;
  country?: string;
  tradeName?: string;
  billingPhone?: string;
  addressLine2?: string;
}

export interface PlanUpdatePayload {
  name?: string;
  description?: string | null;
  maxUsers?: number | null;
  priceCents?: number | null;
  currency?: string;
  billingCycleMonths?: number;
  isActive?: boolean;
}

export interface CompanyUpdatePayload {
  legalName?: string;
  tradeName?: string | null;
  taxId?: string;
  billingEmail?: string;
  billingPhone?: string | null;
  addressLine1?: string;
  addressLine2?: string | null;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  isActive?: boolean;
}

export async function fetchTenants(
  token: string,
  includeInactive = false
): Promise<TenantSummary[]> {
  const query = includeInactive ? '?include_inactive=true' : '';
  return apiFetch<TenantSummary[]>(`/v1/admin/tenants${query}`, { token });
}

export async function fetchPlans(
  token: string,
  includeInactive = false
): Promise<CommercialPlan[]> {
  const query = includeInactive ? '?include_inactive=true' : '';
  return apiFetch<CommercialPlan[]>(`/v1/admin/plans${query}`, { token });
}

export async function updatePlan(
  token: string,
  planId: string,
  payload: PlanUpdatePayload
): Promise<CommercialPlan> {
  return apiFetch<CommercialPlan>(`/v1/admin/plans/${planId}`, {
    token,
    method: 'PATCH',
    body: payload,
  });
}

export async function fetchCompanies(
  token: string,
  tenantId: string,
  includeInactive = false
): Promise<TenantCompany[]> {
  const query = includeInactive ? '?include_inactive=true' : '';
  return apiFetch<TenantCompany[]>(
    `/v1/admin/tenants/${tenantId}/companies${query}`,
    { token }
  );
}

export async function attachCompanies(
  token: string,
  tenantId: string,
  companies: CompanyCreatePayload[]
): Promise<TenantCompany[]> {
  return apiFetch<TenantCompany[]>(`/v1/admin/tenants/${tenantId}/companies`, {
    token,
    method: 'POST',
    body: { companies },
  });
}

export async function updateCompany(
  token: string,
  companyId: string,
  payload: CompanyUpdatePayload
): Promise<TenantCompany> {
  return apiFetch<TenantCompany>(`/v1/admin/companies/${companyId}`, {
    token,
    method: 'PATCH',
    body: payload,
  });
}

export async function fetchUsers(
  token: string,
  tenantId: string,
  includeInactive = false
): Promise<AdminUserAccount[]> {
  const query = includeInactive ? '?include_inactive=true' : '';
  return apiFetch<AdminUserAccount[]>(`/v1/t/${tenantId}/admin/users${query}`, {
    token,
  });
}

export async function suspendUser(
  token: string,
  tenantId: string,
  userId: string,
  reason?: string
): Promise<AdminUserAccount> {
  return apiFetch<AdminUserAccount>(
    `/v1/t/${tenantId}/admin/users/${userId}/suspend`,
    {
      token,
      method: 'POST',
      body: reason ? { reason } : {},
    }
  );
}

export async function reinstateUser(
  token: string,
  tenantId: string,
  userId: string,
  reactivate = false
): Promise<AdminUserAccount> {
  return apiFetch<AdminUserAccount>(
    `/v1/t/${tenantId}/admin/users/${userId}/reinstate`,
    {
      token,
      method: 'POST',
      body: { reactivate },
    }
  );
}

export async function initiatePasswordReset(
  token: string,
  tenantId: string,
  userId: string
): Promise<PasswordResetTokenPayload> {
  return apiFetch<PasswordResetTokenPayload>(
    `/v1/t/${tenantId}/admin/users/${userId}/reset-password`,
    {
      token,
      method: 'POST',
    }
  );
}

export async function confirmPasswordReset(
  token: string,
  tenantId: string,
  userId: string,
  resetToken: string,
  newPassword: string
): Promise<AdminUserAccount> {
  return apiFetch<AdminUserAccount>(
    `/v1/t/${tenantId}/admin/users/${userId}/reset-password/confirm`,
    {
      token,
      method: 'POST',
      body: { token: resetToken, newPassword },
    }
  );
}
