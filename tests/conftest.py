import pytest
from fastapi.testclient import TestClient

from app.api.routes import benchmarking as benchmarking_routes
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import create_app
from app.middleware.rate_limit import RateLimitMiddleware

TENANT_ID = "11111111-1111-1111-1111-111111111111"
USER_ID = "44444444-4444-4444-4444-444444444444"

settings = get_settings()
settings.rate_limit_requests = 5
settings.rate_limit_window_seconds = 60

app = create_app()


def _override_get_db():
    yield None


def _get_rate_limiter(asgi_app) -> RateLimitMiddleware | None:
    middleware = asgi_app.middleware_stack
    while hasattr(middleware, "app"):
        if isinstance(middleware, RateLimitMiddleware):
            return middleware
        middleware = middleware.app
    return None


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _clear_state():
    repository = benchmarking_routes.service.repository
    clear = getattr(repository, "clear", None)
    if callable(clear):
        clear()
    rate_limiter = _get_rate_limiter(app)
    if rate_limiter:
        rate_limiter.reset()
    yield
    if callable(clear):
        clear()
    if rate_limiter:
        rate_limiter.reset()


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    token = create_access_token(
        subject=USER_ID,
        extra_claims={"tenant_id": TENANT_ID, "roles": ["user"]},
    )
    return {"Authorization": f"Bearer {token}"}
