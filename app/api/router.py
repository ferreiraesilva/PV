from fastapi import APIRouter

from app.api.routes import (
    administration,
    auth,
    benchmarking,
    financial_index,
    health,
    simulations,
    valuations,
    admin_portal,
)

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/t/{tenant_id}")
api_router.include_router(administration.router)
api_router.include_router(simulations.router)
api_router.include_router(valuations.router)
api_router.include_router(benchmarking.router)
api_router.include_router(financial_index.router)
api_router.include_router(admin_portal.superuser_router, prefix="/admin-portal")
api_router.include_router(admin_portal.tenant_admin_router, prefix="/admin-portal")
