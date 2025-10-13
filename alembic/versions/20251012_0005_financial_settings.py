"""financial_settings

Revision ID: 8f7b7e7e7e7e
Revises: 20251006_0004_payment_plan_templates
Create Date: 2025-10-12 00:00:00.000000

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f7b7e7e7e7e"
down_revision: str | None = "20251006_0004_payment_plan_templates"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "financial_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("periods_per_year", sa.Integer(), nullable=True),
        sa.Column("default_multiplier", sa.Numeric(8, 4), nullable=True),
        sa.Column("cancellation_multiplier", sa.Numeric(8, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_index(
        op.f("ix_financial_settings_id"), "financial_settings", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_financial_settings_tenant_id"),
        "financial_settings",
        ["tenant_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_financial_settings_tenant_id"), table_name="financial_settings"
    )
    op.drop_index(op.f("ix_financial_settings_id"), table_name="financial_settings")
    op.drop_table("financial_settings")
