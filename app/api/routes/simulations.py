from __future__ import annotations

from typing import Iterable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import CurrentUser, require_roles
from app.api.schemas.simulation import (
    InstallmentInput,
    SimulationBatchRequest,
    SimulationBatchResponse,
    SimulationInput,
    SimulationOutcome,
    SimulationPlanSnapshot,
    SimulationResult,
)
from app.db.repositories.payment_plan_template import PaymentPlanTemplateRepository
from app.db.session import get_db
from app.services.simulation import SimulationPlan

router = APIRouter(tags=["Simulations"], prefix="/t/{tenant_id}")


def _record_audit(request: Request, response: SimulationBatchResponse) -> None:
    payload = response.model_dump()
    request.state.audit_resource_type = "simulation_calculation"
    request.state.audit_resource_id = "batch"
    request.state.audit_payload_out = {"outcomes": payload.get("outcomes", [])}
    request.state.audit_diffs = {"outcomes": payload.get("outcomes", [])}


def _run_simulation(plan: SimulationPlan) -> SimulationResult:
    metrics = plan.metrics()
    return SimulationResult(**metrics)


def _snapshot(principal: float, discount_rate: float, installments: Iterable[InstallmentInput]) -> SimulationPlanSnapshot:
    normalized = [InstallmentInput(period=item.period, amount=item.amount) for item in installments]
    return SimulationPlanSnapshot(principal=principal, discount_rate=discount_rate, installments=normalized)


@router.post("/simulations", response_model=SimulationBatchResponse)
def create_simulation(
    tenant_id: str,
    payload: SimulationBatchRequest | SimulationInput,
    request: Request,
    db=Depends(get_db),
    current_user: CurrentUser = Depends(require_roles("user", "superuser")),
) -> SimulationBatchResponse:
    request.state.audit_actor_roles = current_user.roles
    request.state.audit_actor_user_id = current_user.user_id

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant identifier") from exc

    if isinstance(payload, SimulationInput):
        plan = SimulationPlan(
            principal=payload.principal,
            discount_rate=payload.discount_rate,
            periods=[(item.period, item.amount) for item in payload.installments],
        )
        result = _run_simulation(plan)
        response = SimulationBatchResponse(
            tenant_id=tenant_id,
            outcomes=[
                SimulationOutcome(
                    source="input",
                    plan_key=None,
                    label=None,
                    product_code=None,
                    template_id=None,
                    plan=_snapshot(payload.principal, payload.discount_rate, payload.installments),
                    result=result,
                )
            ],
        )
        _record_audit(request, response)
        return response

    batch = payload
    repository = PaymentPlanTemplateRepository(db)

    requested_ids = {ref.template_id for ref in batch.templates if ref.template_id is not None}
    requested_codes = {ref.product_code.lower() for ref in batch.templates if ref.product_code}
    requested_codes.update(
        plan.product_code.strip().lower()
        for plan in batch.plans
        if plan.product_code and plan.product_code.strip()
    )

    templates_by_id: dict[UUID, object] = {}
    templates_by_code: dict[str, object] = {}

    for template in repository.list_by_ids(tenant_uuid, requested_ids):
        templates_by_id[template.id] = template
        templates_by_code[template.product_code.lower()] = template

    for template in repository.list_by_product_codes(tenant_uuid, requested_codes):
        templates_by_id[template.id] = template
        templates_by_code[template.product_code.lower()] = template

    outcomes: list[SimulationOutcome] = []
    included_template_ids: set[UUID] = set()

    for plan_payload in batch.plans:
        plan = SimulationPlan(
            principal=plan_payload.principal,
            discount_rate=plan_payload.discount_rate,
            periods=[(item.period, item.amount) for item in plan_payload.installments],
        )
        result = _run_simulation(plan)
        plan_product_code = plan_payload.product_code.strip() if plan_payload.product_code else None
        outcomes.append(
            SimulationOutcome(
                source="input",
                plan_key=plan_payload.key,
                label=plan_payload.label,
                product_code=plan_product_code,
                template_id=None,
                plan=_snapshot(plan_payload.principal, plan_payload.discount_rate, plan_payload.installments),
                result=result,
            )
        )

        if plan_product_code:
            template = templates_by_code.get(plan_product_code.lower())
            if template and template.id not in included_template_ids:
                template_plan = SimulationPlan(
                    principal=float(template.principal),
                    discount_rate=float(template.discount_rate),
                    periods=[(item.period, float(item.amount)) for item in template.installments],
                )
                template_result = _run_simulation(template_plan)
                outcomes.append(
                    SimulationOutcome(
                        source="template",
                        plan_key=plan_payload.key,
                        label=template.name,
                        product_code=template.product_code,
                        template_id=template.id,
                        plan=_snapshot(
                            float(template.principal),
                            float(template.discount_rate),
                            [
                                InstallmentInput(period=item.period, amount=float(item.amount))
                                for item in template.installments
                            ],
                        ),
                        result=template_result,
                    )
                )
                included_template_ids.add(template.id)

    for ref in batch.templates:
        template = None
        if ref.template_id is not None:
            template = templates_by_id.get(ref.template_id)
        elif ref.product_code and ref.product_code.strip():
            template = templates_by_code.get(ref.product_code.strip().lower())
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment plan template not found")
        if template.id in included_template_ids:
            continue
        template_plan = SimulationPlan(
            principal=float(template.principal),
            discount_rate=float(template.discount_rate),
            periods=[(item.period, float(item.amount)) for item in template.installments],
        )
        template_result = _run_simulation(template_plan)
        outcomes.append(
            SimulationOutcome(
                source="template",
                plan_key=None,
                label=template.name,
                product_code=template.product_code,
                template_id=template.id,
                plan=_snapshot(
                    float(template.principal),
                    float(template.discount_rate),
                    [
                        InstallmentInput(period=item.period, amount=float(item.amount))
                        for item in template.installments
                    ],
                ),
                result=template_result,
            )
        )
        included_template_ids.add(template.id)

    response = SimulationBatchResponse(tenant_id=tenant_id, outcomes=outcomes)
    _record_audit(request, response)
    return response


