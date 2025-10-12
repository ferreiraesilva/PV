"""Administrative lifecycle enhancements"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251006_0003"
down_revision: Union[str, None] = "20251005_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_suspended", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "users",
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("suspension_reason", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("password_reset_token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_token_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "password_reset_requested_at", sa.DateTime(timezone=True), nullable=True
        ),
    )

    op.execute("UPDATE users SET is_suspended = FALSE WHERE is_suspended IS NULL")
    op.alter_column("users", "is_suspended", server_default=None)

    op.execute(
        """
        UPDATE tenants
        SET is_default = TRUE
        WHERE id = '11111111-1111-1111-1111-111111111111'
        """
    )


def downgrade() -> None:
    op.drop_column("users", "password_reset_requested_at")
    op.drop_column("users", "password_reset_token_expires_at")
    op.drop_column("users", "password_reset_token_hash")
    op.drop_column("users", "suspension_reason")
    op.drop_column("users", "suspended_at")
    op.drop_column("users", "is_suspended")
