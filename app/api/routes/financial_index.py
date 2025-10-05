from __future__ import annotations

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import CurrentUser, SessionDependency, require_roles
from app.api.schemas.financial_index import IndexValueBatchInput, IndexValueOutput
from app.services.administration import ActingUser, PermissionDeniedError
from app.services.financial_index import FinancialIndexService

router = APIRouter(tags=["Financial Indexes"], prefix="/t/{tenant_id}/indexes")


def get_financial_index_service(db: SessionDependency) -> FinancialIndexService:
    return FinancialIndexService(db)


ServiceDependency = Annotated[FinancialIndexService, Depends(get_financial_index_service)]


def _acting_user(current_user: CurrentUser) -> ActingUser:
    return ActingUser(id=current_user.user_id, tenant_id=current_user.tenant_id, roles=frozenset(current_user.roles))


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, PermissionDeniedError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    raise exc


@router.post("/{index_code}/values", response_model=List[IndexValueOutput], status_code=status.HTTP_201_CREATED)
def create_or_update_index_values(
    tenant_id: UUID,
    index_code: str,
    service: ServiceDependency,
    payload: IndexValueBatchInput,
    current_user: CurrentUser = Depends(require_roles("tenant_admin", "superuser")),
) -> List[IndexValueOutput]:
    """Cria ou atualiza valores para um índice financeiro customizado do tenant."""
    acting = _acting_user(current_user)
    try:
        results = service.create_or_update_values(acting, tenant_id, index_code, payload.values)
    except Exception as exc:
        _handle_service_error(exc)
    return [IndexValueOutput.model_validate(r) for r in results]


@router.get("/{index_code}/values", response_model=List[IndexValueOutput])
def list_index_values(
    tenant_id: UUID,
    index_code: str,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(require_roles("tenant_admin", "superuser", "support")),
) -> List[IndexValueOutput]:
    """Lista os valores históricos de um índice financeiro customizado do tenant."""
    acting = _acting_user(current_user)
    try:
        results = service.list_values(acting, tenant_id, index_code)
    except Exception as exc:
        _handle_service_error(exc)
    return [IndexValueOutput.model_validate(r) for r in results]