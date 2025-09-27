from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, generate_latest
from starlette.responses import Response

from app.api.router import api_router
from app.audit.middleware import AuditMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
registry = CollectorRegistry()
request_counter = Counter(
    "safv_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)


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

    app.add_middleware(AuditMiddleware)
    app.include_router(api_router)

    @app.middleware("http")
    async def track_requests(request, call_next):
        response = await call_next(request)
        request_counter.labels(request.method, request.url.path, str(response.status_code)).inc()
        return response

    @app.get("/metrics", tags=["Health"], summary="Prometheus metrics feed")
    async def metrics() -> Response:
        data = generate_latest(registry)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()

