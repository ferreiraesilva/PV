from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.router import api_router
from app.audit.middleware import AuditMiddleware
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.observability.metrics import REQUEST_COUNTER, observe_request, registry, now_seconds

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, version=settings.environment, lifespan=lifespan)

    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
        excluded_paths={"/metrics", "/v1/health"},
    )
    app.add_middleware(AuditMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router)

    @app.middleware("http")
    async def track_requests(request, call_next):
        start = now_seconds()
        response = await call_next(request)
        duration = now_seconds() - start
        REQUEST_COUNTER.labels(request.method, request.url.path, str(response.status_code)).inc()
        observe_request(request.url.path, duration)
        return response

    @app.get("/metrics", tags=["Health"], summary="Prometheus metrics feed")
    async def metrics() -> Response:
        data = generate_latest(registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
