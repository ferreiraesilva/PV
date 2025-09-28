from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, require_roles
from app.api.schemas.simulation import SimulationInput, SimulationResponse
from app.db.session import get_db
from app.services.simulation import SimulationPlan

router = APIRouter(tags=["Simulations"], prefix="/t/{tenant_id}")


def _record_audit(request: Request, payload: dict) -> None:
    result_only = {"result": payload.get("result")}
    request.state.audit_payload_out = result_only
    request.state.audit_diffs = {"computed": payload.get("result")}
    request.state.audit_resource_type = "simulation_calculation"


@router.post("/simulations", response_model=SimulationResponse)
def create_simulation(
    tenant_id: str,
    payload: SimulationInput,
    request: Request,
    db=Depends(get_db),  # noqa: ARG001
    current_user: CurrentUser = Depends(require_roles("user", "superuser")),
) -> SimulationResponse:
    request.state.audit_actor_roles = current_user.roles
    request.state.audit_actor_user_id = current_user.user_id

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
