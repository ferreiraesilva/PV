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
  period: number;
  amount: number;
}

export interface SimulationRequest {
  principal: number;
  discount_rate: number;
  installments: SimulationInstallment[];
}

export interface SimulationResult {
  present_value: number;
  future_value: number;
  payment: number;
  average_installment: number;
  mean_term_months: number;
}

export interface SimulationResponse {
  tenant_id: string;
  plan: SimulationRequest;
  result: SimulationResult;
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
