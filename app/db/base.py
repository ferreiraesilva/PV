from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# Import models here so Alembic can discover metadata
try:
    from app.db.models import audit_log, commercial_plan, refresh_token, tenant, tenant_company, tenant_plan_subscription, user  # noqa: F401
except ImportError:
    pass
