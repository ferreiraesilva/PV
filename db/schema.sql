-- safv database schema
-- Generated for ETAPA 2

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(320) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    locale VARCHAR(16) DEFAULT 'en-US',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, email)
);

CREATE INDEX ix_users_tenant_id ON users (tenant_id);
CREATE INDEX ix_users_email ON users (email);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    user_agent TEXT,
    ip_address INET,
    UNIQUE (token_hash)
);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at);

CREATE TABLE financial_indices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    source VARCHAR(255),
    unit VARCHAR(32),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, code)
);

CREATE UNIQUE INDEX uq_financial_indices_code_global ON financial_indices (code) WHERE tenant_id IS NULL;

CREATE TABLE financial_index_values (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    financial_index_id UUID NOT NULL REFERENCES financial_indices(id) ON DELETE CASCADE,
    reference_date DATE NOT NULL,
    value NUMERIC(14,6) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (financial_index_id, reference_date)
);

CREATE INDEX ix_financial_index_values_date ON financial_index_values (reference_date);

CREATE TABLE simulation_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_amount NUMERIC(18,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'BRL',
    valuation_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','processing','completed','failed')),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_simulation_requests_tenant_id ON simulation_requests (tenant_id);
CREATE INDEX ix_simulation_requests_status ON simulation_requests (status);

CREATE TABLE simulation_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    simulation_request_id UUID NOT NULL REFERENCES simulation_requests(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    discount_rate NUMERIC(8,4) NOT NULL,
    rate_type VARCHAR(50) NOT NULL,
    indexation_formula TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (simulation_request_id, name)
);

CREATE INDEX ix_simulation_plans_request_id ON simulation_plans (simulation_request_id);

CREATE TABLE simulation_plan_installments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    simulation_plan_id UUID NOT NULL REFERENCES simulation_plans(id) ON DELETE CASCADE,
    sequence SMALLINT NOT NULL,
    due_date DATE NOT NULL,
    principal_amount NUMERIC(18,2) NOT NULL,
    interest_rate NUMERIC(8,4),
    financial_index_id UUID REFERENCES financial_indices(id) ON DELETE SET NULL,
    is_adjustable BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (simulation_plan_id, sequence)
);

CREATE INDEX ix_plan_installments_plan_id ON simulation_plan_installments (simulation_plan_id);
CREATE INDEX ix_plan_installments_due_date ON simulation_plan_installments (due_date);

CREATE TABLE simulation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    simulation_plan_id UUID NOT NULL REFERENCES simulation_plans(id) ON DELETE CASCADE,
    present_value NUMERIC(18,2) NOT NULL,
    average_installment NUMERIC(18,2),
    mean_term_months NUMERIC(10,2),
    future_value NUMERIC(18,2),
    summary JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (simulation_plan_id)
);

CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    valuation_date DATE NOT NULL,
    discount_rate NUMERIC(8,4) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','processing','completed','failed')),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_portfolio_snapshots_tenant_id ON portfolio_snapshots (tenant_id);

CREATE TABLE portfolio_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES portfolio_snapshots(id) ON DELETE CASCADE,
    external_id VARCHAR(128),
    customer_code VARCHAR(128),
    segment VARCHAR(128),
    risk_score NUMERIC(5,2),
    probability_default NUMERIC(5,4) CHECK (probability_default BETWEEN 0 AND 1),
    probability_cancellation NUMERIC(5,4) CHECK (probability_cancellation BETWEEN 0 AND 1),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_portfolio_contracts_snapshot_id ON portfolio_contracts (snapshot_id);
CREATE INDEX ix_portfolio_contracts_customer_code ON portfolio_contracts (customer_code);

CREATE TABLE portfolio_cashflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    contract_id UUID NOT NULL REFERENCES portfolio_contracts(id) ON DELETE CASCADE,
    due_date DATE NOT NULL,
    amount_due NUMERIC(18,2) NOT NULL,
    expected_payment_date DATE,
    paid_amount NUMERIC(18,2),
    paid_date DATE,
    status VARCHAR(32) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','paid','overdue','cancelled')),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (contract_id, due_date, amount_due)
);

CREATE INDEX ix_portfolio_cashflows_contract_id ON portfolio_cashflows (contract_id);
CREATE INDEX ix_portfolio_cashflows_due_date ON portfolio_cashflows (due_date);

CREATE TABLE portfolio_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES portfolio_snapshots(id) ON DELETE CASCADE,
    gross_present_value NUMERIC(18,2) NOT NULL,
    net_present_value NUMERIC(18,2) NOT NULL,
    expected_losses NUMERIC(18,2),
    pricing_value NUMERIC(18,2),
    scenario VARCHAR(32) NOT NULL,
    metrics JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (snapshot_id, scenario)
);

CREATE TABLE benchmark_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    reference_month DATE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','processing','completed','failed')),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, reference_month)
);

CREATE TABLE benchmark_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    benchmark_batch_id UUID NOT NULL REFERENCES benchmark_batches(id) ON DELETE CASCADE,
    metric_code VARCHAR(100) NOT NULL,
    segment VARCHAR(128),
    region VARCHAR(128),
    value_numeric NUMERIC(18,4),
    value_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_benchmark_metrics_batch_id ON benchmark_metrics (benchmark_batch_id);
CREATE INDEX ix_benchmark_metrics_metric ON benchmark_metrics (metric_code);

CREATE TABLE recommendation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    snapshot_id UUID REFERENCES portfolio_snapshots(id) ON DELETE SET NULL,
    simulation_request_id UUID REFERENCES simulation_requests(id) ON DELETE SET NULL,
    run_type VARCHAR(50) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','processing','completed','failed')),
    notes TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE recommendation_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_run_id UUID NOT NULL REFERENCES recommendation_runs(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(32) CHECK (priority IN ('low','medium','high','critical')),
    action_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_recommendation_items_run_id ON recommendation_items (recommendation_run_id);

CREATE TABLE audit_logs (
    id BIGSERIAL NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id UUID NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    role VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    method VARCHAR(10) NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    payload_in JSONB,
    payload_out JSONB,
    resource_type VARCHAR(120),
    resource_id VARCHAR(120),
    diffs JSONB,
    metadata JSONB,
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

CREATE TABLE audit_logs_default PARTITION OF audit_logs DEFAULT;

CREATE INDEX ix_audit_logs_tenant_id ON audit_logs (tenant_id);
CREATE INDEX ix_audit_logs_request_id ON audit_logs (request_id);
CREATE INDEX ix_audit_logs_occurred_at ON audit_logs (occurred_at);

-- Suggested retention and partitioning policy for audit_logs:
-- 1. Create monthly partitions via: 
--    CREATE TABLE audit_logs_2025_09 PARTITION OF audit_logs
--    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');
-- 2. Schedule a local job to detach and archive partitions older than 24 months.
-- 3. Use BRIN indexes per partition to reduce maintenance overhead.

