export interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface TokenRefreshResponse {
  access_token: string;
  expires_in: number;
}

export interface SimulationInstallment {
  due_date: string;
  amount: number;
}

export interface AdjustmentPayload {
  base_date: string;
  index: string;
  periodicity: 'monthly' | 'anniversary';
  addon_rate: number;
}

export interface SimulationPlanPayload {
  key?: string;
  label?: string;
  product_code?: string;
  principal: number;
  discount_rate: number;
  adjustment?: AdjustmentPayload;
  installments: SimulationInstallment[];
}

export interface SimulationTemplateReference {
  template_id?: string;
  product_code?: string;
}

export interface SimulationBatchRequest {
  plans: SimulationPlanPayload[];
  templates?: SimulationTemplateReference[];
}

export interface SimulationResult {
  present_value: number;
  present_value_adjusted?: number;
  future_value: number;
  payment: number;
  average_installment: number;
  mean_term_months: number;
}

export interface SimulationPlanSnapshot {
  principal: number;
  discount_rate: number;
  installments: SimulationInstallment[];
}

export interface SimulationOutcome {
  source: 'input' | 'template';
  plan_key?: string | null;
  label?: string | null;
  product_code?: string | null;
  template_id?: string | null;
  result: SimulationResult;
  plan: SimulationPlanSnapshot;
}

export interface SimulationBatchResponse {
  tenant_id: string;
  outcomes: SimulationOutcome[];
}

export interface ValuationCashflowInput {
  due_date: string;
  amount: number;
  probability_default: number;
  probability_cancellation: number;
}

export interface ValuationScenarioInput {
  code: string;
  discount_rate: number;
  default_multiplier: number;
  cancellation_multiplier: number;
}

export interface ValuationRequest {
  cashflows: ValuationCashflowInput[];
  scenarios: ValuationScenarioInput[];
}

export interface ValuationScenarioResult {
  code: string;
  gross_present_value: number;
  net_present_value: number;
  expected_losses: number;
}

export interface ValuationResponse {
  tenant_id: string;
  results: ValuationScenarioResult[];
}

export interface BenchmarkAggregationItem {
  metricCode: string;
  segmentBucket: string;
  regionBucket: string;
  count: number;
  averageValue: number;
  minValue: number;
  maxValue: number;
}

export interface BenchmarkIngestResponse {
  tenantId: string;
  batchId: string;
  totalRows: number;
  discardedRows: number;
  aggregations: BenchmarkAggregationItem[];
}

export interface BenchmarkAggregationsResponse {
  tenantId: string;
  batchId: string;
  aggregations: BenchmarkAggregationItem[];
}

export interface CalculationJobStatus {
  jobId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  submittedAt: string;
  completedAt?: string | null;
  message?: string;
}

export interface RecommendationRunCreate {
  runType: string;
  snapshotId?: string;
  simulationId?: string;
  parameters?: Record<string, unknown>;
}

export interface RecommendationRunItem {
  title: string;
  description: string;
  priority: string;
}

export interface RecommendationRunResponse {
  runId: string;
  tenantId: string;
  snapshotId?: string | null;
  simulationId?: string | null;
  runType: string;
  status: string;
  notes?: string;
  items: RecommendationRunItem[];
  createdAt: string;
  completedAt?: string | null;
}

export interface IndexValueInput {
  reference_date: string;
  value: number;
}

export interface IndexValueBatchInput {
  values: IndexValueInput[];
}

export interface IndexValueOutput {
  reference_date: string;
  value: number;
  updated_at: string;
}

export interface AuditLogEntry {
  id: number;
  occurredAt: string;
  requestId: string;
  tenantId: string;
  userId?: string | null;
  method: string;
  endpoint: string;
  statusCode: number;
}

export interface TenantSummary {
  id: string;
  name: string;
  slug: string;
  isActive: boolean;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CommercialPlan {
  id: string;
  tenantId: string;
  name: string;
  description?: string | null;
  maxUsers?: number | null;
  priceCents?: number | null;
  currency: string;
  isActive: boolean;
  billingCycleMonths: number;
  createdAt: string;
  updatedAt: string;
}

export interface TenantCompany {
  id: string;
  tenantId: string;
  legalName: string;
  tradeName?: string | null;
  taxId: string;
  billingEmail: string;
  billingPhone?: string | null;
  addressLine1: string;
  addressLine2?: string | null;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AdminUserAccount {
  id: string;
  tenantId: string;
  email: string;
  fullName?: string | null;
  roles: string[];
  isActive: boolean;
  isSuperuser: boolean;
  isSuspended?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface PasswordResetTokenPayload {
  token: string;
  expiresAt: string;
}
