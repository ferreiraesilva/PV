"""Add payment plan templates support"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251006_0004"
down_revision: Union[str, None] = "20251006_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_plan_templates",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("principal", sa.Numeric(18, 4), nullable=False),
        sa.Column(
            "discount_rate", sa.Numeric(10, 6), nullable=False, server_default="0"
        ),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id", "product_code", name="uq_payment_plan_templates_product"
        ),
    )

    op.create_table(
        "payment_plan_installments",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payment_plan_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.UniqueConstraint(
            "template_id", "period", name="uq_payment_plan_installments_period"
        ),
    )


def downgrade() -> None:
    op.drop_table("payment_plan_installments")
    op.drop_table("payment_plan_templates")
