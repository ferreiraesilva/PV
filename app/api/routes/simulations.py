from fastapi import APIRouter, Depends, Request

from app.api.schemas.simulation import SimulationInput, SimulationResponse
from app.db.session import get_db
from app.services.simulation import SimulationPlan

router = APIRouter(tags=["Simulations"], prefix="/t/{tenant_id}")


def _record_audit(request: Request, payload: dict) -> None:
    request.state.audit_payload_out = payload
    request.state.audit_diffs = payload


@router.post("/simulations", response_model=SimulationResponse)
def create_simulation(tenant_id: str, payload: SimulationInput, request: Request, db=Depends(get_db)) -> SimulationResponse:  # noqa: ARG001
    plan = SimulationPlan(
        principal=payload.principal,
        discount_rate=payload.discount_rate,
        periods=[(item.period, item.amount) for item in payload.installments],
    )
    metrics = plan.metrics()
    response = SimulationResponse(
        tenant_id=tenant_id,
        plan=payload,
        result=metrics,
    )
    _record_audit(request, response.model_dump())
    return response
