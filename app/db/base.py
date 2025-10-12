from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# Import models here so Alembic can discover metadata
try:
    from app.db.models import (
        audit_log,  # noqa: F401
        commercial_plan,  # noqa: F401
        refresh_token,  # noqa: F401
        tenant,  # noqa: F401
        tenant_company,  # noqa: F401
        tenant_plan_subscription,  # noqa: F401
        user,  # noqa: F401
    )
except ImportError:
    pass
