"""Initial safv schema"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250927_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=True, server_default=sa.text("'en-US'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("code", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "financial_indices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_financial_indices_tenant_code"),
    )
    op.create_index(
        "uq_financial_indices_code_global",
        "financial_indices",
        ["code"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL"),
    )

    op.create_table(
        "financial_index_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("financial_index_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(14, 6), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["financial_index_id"], ["financial_indices.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("financial_index_id", "reference_date", name="uq_financial_index_values_unique"),
    )
    op.create_index("ix_financial_index_values_date", "financial_index_values", ["reference_date"])

    op.create_table(
        "simulation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'BRL'")),
        sa.Column("valuation_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('draft','processing','completed','failed')", name="ck_simulation_requests_status"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_simulation_requests_tenant_id", "simulation_requests", ["tenant_id"])
    op.create_index("ix_simulation_requests_status", "simulation_requests", ["status"])

    op.create_table(
        "simulation_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("simulation_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("discount_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("rate_type", sa.String(length=50), nullable=False),
        sa.Column("indexation_formula", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["simulation_request_id"], ["simulation_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("simulation_request_id", "name", name="uq_simulation_plans_request_name"),
    )
    op.create_index("ix_simulation_plans_request_id", "simulation_plans", ["simulation_request_id"])

    op.create_table(
        "simulation_plan_installments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("simulation_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.SmallInteger(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("principal_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("interest_rate", sa.Numeric(8, 4), nullable=True),
        sa.Column("financial_index_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_adjustable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["financial_index_id"], ["financial_indices.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["simulation_plan_id"], ["simulation_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("simulation_plan_id", "sequence", name="uq_plan_installments_sequence"),
    )
    op.create_index("ix_plan_installments_plan_id", "simulation_plan_installments", ["simulation_plan_id"])
    op.create_index("ix_plan_installments_due_date", "simulation_plan_installments", ["due_date"])

    op.create_table(
        "simulation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("simulation_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("present_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("average_installment", sa.Numeric(18, 2), nullable=True),
        sa.Column("mean_term_months", sa.Numeric(10, 2), nullable=True),
        sa.Column("future_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["simulation_plan_id"], ["simulation_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("simulation_plan_id", name="uq_simulation_results_plan"),
    )

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("valuation_date", sa.Date(), nullable=False),
        sa.Column("discount_rate", sa.Numeric(8, 4), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('draft','processing','completed','failed')", name="ck_portfolio_snapshots_status"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_portfolio_snapshots_tenant_id", "portfolio_snapshots", ["tenant_id"])

    op.create_table(
        "portfolio_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("customer_code", sa.String(length=128), nullable=True),
        sa.Column("segment", sa.String(length=128), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("probability_default", sa.Numeric(5, 4), nullable=True),
        sa.Column("probability_cancellation", sa.Numeric(5, 4), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("probability_default IS NULL OR (probability_default >= 0 AND probability_default <= 1)", name="ck_contracts_default"),
        sa.CheckConstraint("probability_cancellation IS NULL OR (probability_cancellation >= 0 AND probability_cancellation <= 1)", name="ck_contracts_cancellation"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["portfolio_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_portfolio_contracts_snapshot_id", "portfolio_contracts", ["snapshot_id"])
    op.create_index("ix_portfolio_contracts_customer_code", "portfolio_contracts", ["customer_code"])

    op.create_table(
        "portfolio_cashflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount_due", sa.Numeric(18, 2), nullable=False),
        sa.Column("expected_payment_date", sa.Date(), nullable=True),
        sa.Column("paid_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('scheduled','paid','overdue','cancelled')", name="ck_portfolio_cashflows_status"),
        sa.ForeignKeyConstraint(["contract_id"], ["portfolio_contracts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("contract_id", "due_date", "amount_due", name="uq_cashflows_contract_due_amount"),
    )
    op.create_index("ix_portfolio_cashflows_contract_id", "portfolio_cashflows", ["contract_id"])
    op.create_index("ix_portfolio_cashflows_due_date", "portfolio_cashflows", ["due_date"])

    op.create_table(
        "portfolio_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gross_present_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("net_present_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("expected_losses", sa.Numeric(18, 2), nullable=True),
        sa.Column("pricing_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("scenario", sa.String(length=32), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["snapshot_id"], ["portfolio_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("snapshot_id", "scenario", name="uq_portfolio_results_scenario"),
    )

    op.create_table(
        "benchmark_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reference_month", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('draft','processing','completed','failed')", name="ck_benchmark_batches_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "reference_month", name="uq_benchmark_batches_reference"),
    )

    op.create_table(
        "benchmark_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("benchmark_batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_code", sa.String(length=100), nullable=False),
        sa.Column("segment", sa.String(length=128), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("value_numeric", sa.Numeric(18, 4), nullable=True),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["benchmark_batch_id"], ["benchmark_batches.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_benchmark_metrics_batch_id", "benchmark_metrics", ["benchmark_batch_id"])
    op.create_index("ix_benchmark_metrics_metric", "benchmark_metrics", ["metric_code"])

    op.create_table(
        "recommendation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("simulation_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("run_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('draft','processing','completed','failed')", name="ck_recommendation_runs_status"),
        sa.ForeignKeyConstraint(["simulation_request_id"], ["simulation_requests.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["portfolio_snapshots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "recommendation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("recommendation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=32), nullable=True),
        sa.Column("action_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("priority IS NULL OR priority IN ('low','medium','high','critical')", name="ck_recommendation_items_priority"),
        sa.ForeignKeyConstraint(["recommendation_run_id"], ["recommendation_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_recommendation_items_run_id", "recommendation_items", ["recommendation_run_id"])

    op.execute(
        """
        CREATE TABLE audit_logs (
            id BIGINT NOT NULL,
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
        """
    )
    op.execute("CREATE TABLE IF NOT EXISTS audit_logs_default PARTITION OF audit_logs DEFAULT;")
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_occurred_at", "audit_logs", ["occurred_at"])

    op.execute(
        """
        INSERT INTO tenants (id, name, slug, is_active, metadata, created_at, updated_at)
        VALUES (
            '11111111-1111-1111-1111-111111111111',
            'Default SAFV Tenant',
            'default',
            TRUE,
            jsonb_build_object('notes', 'Bootstrap tenant for local development'),
            NOW(),
            NOW()
        )
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name,
            metadata = EXCLUDED.metadata,
            updated_at = NOW();
        """
    )

    op.execute(
        """
        INSERT INTO permissions (id, code, description)
        VALUES
            ('33333333-3333-3333-3333-333333333331', 'manage_users', 'Allows managing tenant users and roles'),
            ('33333333-3333-3333-3333-333333333332', 'view_audit_logs', 'Allows viewing audit log entries'),
            ('33333333-3333-3333-3333-333333333333', 'manage_financial_models', 'Allows maintaining financial models and indices')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO roles (id, tenant_id, name, description, is_default, created_at)
        VALUES (
            '22222222-2222-2222-2222-222222222222',
            '11111111-1111-1111-1111-111111111111',
            'tenant_admin',
            'Full administrative role for SAFV tenant',
            TRUE,
            NOW()
        )
        ON CONFLICT (tenant_id, name) DO UPDATE SET
            description = EXCLUDED.description,
            is_default = EXCLUDED.is_default;
        """
    )

    op.execute(
        """
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT '22222222-2222-2222-2222-222222222222', perm.id
        FROM permissions perm
        WHERE perm.code IN ('manage_users', 'view_audit_logs', 'manage_financial_models')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO users (id, tenant_id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at)
        VALUES (
            '44444444-4444-4444-4444-444444444444',
            '11111111-1111-1111-1111-111111111111',
            'admin@labs4ideas.com.br',
            '$2b$12$Y3gvmmuiRrJ5gDLUBxKMk.rYfX7UykHSpL9PiW3fVGPoL0Lbvm/VW',
            'Default SAFV Admin',
            TRUE,
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (tenant_id, email) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            is_active = TRUE,
            is_superuser = TRUE,
            updated_at = NOW();
        """
    )

    op.execute(
        """
        INSERT INTO user_roles (user_id, role_id, assigned_at)
        VALUES (
            '44444444-4444-4444-4444-444444444444',
            '22222222-2222-2222-2222-222222222222',
            NOW()
        )
        ON CONFLICT (user_id, role_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM user_roles WHERE user_id = '44444444-4444-4444-4444-444444444444' AND role_id = '22222222-2222-2222-2222-222222222222';")
    op.execute("DELETE FROM users WHERE id = '44444444-4444-4444-4444-444444444444';")
    op.execute("DELETE FROM role_permissions WHERE role_id = '22222222-2222-2222-2222-222222222222';")
    op.execute("DELETE FROM roles WHERE id = '22222222-2222-2222-2222-222222222222';")
    op.execute("DELETE FROM permissions WHERE code IN ('manage_users','view_audit_logs','manage_financial_models');")
    op.execute("DELETE FROM tenants WHERE id = '11111111-1111-1111-1111-111111111111';")

    op.drop_index("ix_audit_logs_occurred_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.execute("DROP TABLE IF EXISTS audit_logs_default;")
    op.execute("DROP TABLE IF EXISTS audit_logs;")

    op.drop_index("ix_recommendation_items_run_id", table_name="recommendation_items")
    op.drop_table("recommendation_items")
    op.drop_table("recommendation_runs")

    op.drop_index("ix_benchmark_metrics_metric", table_name="benchmark_metrics")
    op.drop_index("ix_benchmark_metrics_batch_id", table_name="benchmark_metrics")
    op.drop_table("benchmark_metrics")
    op.drop_table("benchmark_batches")

    op.drop_table("portfolio_results")
    op.drop_index("ix_portfolio_cashflows_due_date", table_name="portfolio_cashflows")
    op.drop_index("ix_portfolio_cashflows_contract_id", table_name="portfolio_cashflows")
    op.drop_table("portfolio_cashflows")
    op.drop_index("ix_portfolio_contracts_customer_code", table_name="portfolio_contracts")
    op.drop_index("ix_portfolio_contracts_snapshot_id", table_name="portfolio_contracts")
    op.drop_table("portfolio_contracts")
    op.drop_index("ix_portfolio_snapshots_tenant_id", table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")

    op.drop_table("simulation_results")
    op.drop_index("ix_plan_installments_due_date", table_name="simulation_plan_installments")
    op.drop_index("ix_plan_installments_plan_id", table_name="simulation_plan_installments")
    op.drop_table("simulation_plan_installments")
    op.drop_index("ix_simulation_plans_request_id", table_name="simulation_plans")
    op.drop_table("simulation_plans")
    op.drop_index("ix_simulation_requests_status", table_name="simulation_requests")
    op.drop_index("ix_simulation_requests_tenant_id", table_name="simulation_requests")
    op.drop_table("simulation_requests")

    op.drop_index("ix_financial_index_values_date", table_name="financial_index_values")
    op.drop_table("financial_index_values")
    op.drop_index("uq_financial_indices_code_global", table_name="financial_indices")
    op.drop_table("financial_indices")

    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_table("users")
    op.drop_table("tenants")

    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
