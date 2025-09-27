from fastapi import APIRouter, Depends, Request

from app.api.schemas.simulation import CashflowInput, ScenarioResult, ValuationInput, ValuationResponse
from app.db.session import get_db
from app.services.financial import Cashflow
from app.services.simulation import PortfolioScenario, evaluate_portfolio

router = APIRouter(tags=["Valuations"], prefix="/t/{tenant_id}")


def _record_audit(request: Request, payload: dict) -> None:
    request.state.audit_payload_out = payload
    request.state.audit_diffs = payload


@router.post("/valuations/snapshots/{snapshot_id}/results", response_model=ValuationResponse)
def evaluate_snapshot(tenant_id: str, snapshot_id: str, payload: ValuationInput, request: Request, db=Depends(get_db)) -> ValuationResponse:  # noqa: ARG001
    cashflows = [
        Cashflow(
            due_date=item.due_date,
            amount=item.amount,
            probability_default=item.probability_default,
            probability_cancellation=item.probability_cancellation,
        )
        for item in payload.cashflows
    ]

    results = []
    for scenario in payload.scenarios:
        scenario_result = evaluate_portfolio(
            cashflows,
            PortfolioScenario(
                discount_rate=scenario.discount_rate,
                default_multiplier=scenario.default_multiplier,
                cancellation_multiplier=scenario.cancellation_multiplier,
            ),
        )
        results.append(ScenarioResult(code=scenario.code, **scenario_result))

    response = ValuationResponse(tenant_id=tenant_id, results=results)
    _record_audit(request, response.model_dump())
    return response
