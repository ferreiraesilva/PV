"""Add multi-tenant administration structures"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251005_0002"
down_revision: Union[str, None] = "20250927_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "roles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[\"user\"]'::jsonb"),
        ),
    )

    op.alter_column("tenants", "is_default", server_default=None)
    op.alter_column("users", "roles", server_default=None)

    op.create_table(
        "tenant_companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("trade_name", sa.String(length=255), nullable=True),
        sa.Column("tax_id", sa.String(length=32), nullable=False),
        sa.Column("billing_email", sa.String(length=320), nullable=False),
        sa.Column("billing_phone", sa.String(length=32), nullable=True),
        sa.Column("address_line1", sa.String(length=255), nullable=False),
        sa.Column("address_line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("zip_code", sa.String(length=20), nullable=False),
        sa.Column(
            "country",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'BR'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "tax_id", name="uq_tenant_companies_tax_id"),
    )
    op.create_index("ix_tenant_companies_tenant_id", "tenant_companies", ["tenant_id"])

    op.create_table(
        "commercial_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=8),
            nullable=False,
            server_default=sa.text("'BRL'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "billing_cycle_months",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_commercial_plan_tenant_name"),
    )
    op.create_index("ix_commercial_plans_tenant_id", "commercial_plans", ["tenant_id"])

    op.create_table(
        "tenant_plan_subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "activated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("deactivated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["commercial_plans.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_tenant_plan_subscriptions_tenant_id",
        "tenant_plan_subscriptions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_tenant_plan_subscriptions_plan_id", "tenant_plan_subscriptions", ["plan_id"]
    )
    op.create_index(
        "uq_tenant_plan_subscriptions_active",
        "tenant_plan_subscriptions",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_tenant_plan_subscriptions_active", table_name="tenant_plan_subscriptions"
    )
    op.drop_index(
        "ix_tenant_plan_subscriptions_plan_id", table_name="tenant_plan_subscriptions"
    )
    op.drop_index(
        "ix_tenant_plan_subscriptions_tenant_id", table_name="tenant_plan_subscriptions"
    )
    op.drop_table("tenant_plan_subscriptions")

    op.drop_index("ix_commercial_plans_tenant_id", table_name="commercial_plans")
    op.drop_table("commercial_plans")

    op.drop_index("ix_tenant_companies_tenant_id", table_name="tenant_companies")
    op.drop_table("tenant_companies")

    op.drop_column("users", "roles")
    op.drop_column("tenants", "is_default")
