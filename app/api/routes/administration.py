from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status

from app.api.deps import CurrentUser, SessionDependency, require_roles
from app.api.schemas.administration import (
    CommercialPlanResponse,
    CompanyUpdateRequest,
    PasswordResetConfirmRequest,
    PasswordResetResponse,
    PlanAssignRequest,
    PlanCreateRequest,
    PlanUpdateRequest,
    PaymentPlanTemplateCreateRequest,
    PaymentPlanTemplateResponse,
    PaymentPlanTemplateUpdateRequest,
    PaymentPlanInstallmentResponse,
    TenantCompaniesAttachRequest,
    TenantCompanyResponse,
    TenantCreateRequest,
    TenantPlanSubscriptionResponse,
    TenantResponse,
    UserReinstateRequest,
    UserSuspendRequest,
    UserUpdateRequest,
)
from app.api.schemas.user import User as UserResponse, UserCreate
from app.core.roles import SUPERADMIN_ROLE, TENANT_ADMIN_ROLE
from app.services.administration import (
    ActingUser,
    AdministrationService,
    BusinessRuleViolation,
    CompanyInput,
    CompanyUpdateInput,
    NotFoundError,
    PermissionDeniedError,
    PlanCreateInput,
    PlanUpdateInput,
    PaymentPlanInstallmentInput,
    PaymentPlanTemplateCreateInput,
    PaymentPlanTemplateUpdateInput,
    TenantCreateInput,
    UserInput,
    UserUpdateInput,
)

router = APIRouter(tags=["Administration"])


def get_administration_service(db: SessionDependency) -> AdministrationService:
    return AdministrationService(db)


ServiceDependency = Annotated[
    AdministrationService, Depends(get_administration_service)
]


def _acting_user(current_user: CurrentUser) -> ActingUser:
    try:
        return ActingUser(
            id=UUID(current_user.user_id),
            tenant_id=UUID(current_user.tenant_id),
            roles=frozenset(current_user.roles),
        )
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user context"
        ) from exc


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, PermissionDeniedError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    if isinstance(exc, NotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    if isinstance(exc, BusinessRuleViolation):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    raise exc


def _set_audit_actor(request: Request, current_user: CurrentUser) -> None:
    request.state.audit_actor_roles = current_user.roles
    request.state.audit_actor_user_id = current_user.user_id


def _audit_entity(
    request: Request,
    *,
    resource_type: str,
    resource_id: UUID | str,
    payload: Any | None = None,
) -> None:
    request.state.audit_resource_type = resource_type
    request.state.audit_resource_id = str(resource_id)
    if payload is not None:
        if hasattr(payload, "model_dump"):
            request.state.audit_payload_out = payload.model_dump(by_alias=True)
        else:
            request.state.audit_payload_out = payload


def _audit_collection(request: Request, *, resource_type: str, count: int) -> None:
    request.state.audit_resource_type = resource_type
    request.state.audit_resource_id = "collection"
    request.state.audit_payload_out = {"count": count}


def _map_companies(payload: TenantCreateRequest) -> list[CompanyInput]:
    companies: list[CompanyInput] = []
    for company in payload.companies:
        companies.append(
            CompanyInput(
                legal_name=company.legalName,
                trade_name=company.tradeName,
                tax_id=company.taxId,
                billing_email=str(company.billingEmail),
                billing_phone=company.billingPhone,
                address_line1=company.addressLine1,
                address_line2=company.addressLine2,
                city=company.city,
                state=company.state,
                zip_code=company.zipCode,
                country=company.country,
            )
        )
    return companies


def _map_admins(payload: TenantCreateRequest) -> list[UserInput]:
    admins: list[UserInput] = []
    for admin in payload.administrators:
        admins.append(
            UserInput(
                email=admin.email,
                password=admin.password,
                full_name=admin.fullName,
                roles=admin.roles,
            )
        )
    return admins


def _plan_response(plan) -> CommercialPlanResponse:
    return CommercialPlanResponse(
        id=plan.id,
        tenantId=plan.tenant_id,
        name=plan.name,
        description=plan.description,
        maxUsers=plan.max_users,
        priceCents=plan.price_cents,
        currency=plan.currency,
        isActive=plan.is_active,
        billingCycleMonths=plan.billing_cycle_months,
        createdAt=plan.created_at,
        updatedAt=plan.updated_at,
    )


def _payment_plan_template_response(template) -> PaymentPlanTemplateResponse:
    return PaymentPlanTemplateResponse(
        id=template.id,
        tenantId=template.tenant_id,
        productCode=template.product_code,
        name=template.name,
        description=template.description,
        principal=float(template.principal),
        discountRate=float(template.discount_rate),
        metadata=template.metadata_json,
        isActive=template.is_active,
        createdAt=template.created_at,
        updatedAt=template.updated_at,
        installments=[
            PaymentPlanInstallmentResponse(
                id=item.id,
                period=item.period,
                amount=float(item.amount),
            )
            for item in template.installments
        ],
    )


def _tenant_response(tenant) -> TenantResponse:
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        isActive=tenant.is_active,
        isDefault=tenant.is_default,
        createdAt=tenant.created_at,
        updatedAt=tenant.updated_at,
    )


def _subscription_response(subscription) -> TenantPlanSubscriptionResponse:
    return TenantPlanSubscriptionResponse(
        id=subscription.id,
        tenantId=subscription.tenant_id,
        planId=subscription.plan_id,
        isActive=subscription.is_active,
        activatedAt=subscription.activated_at,
        deactivatedAt=subscription.deactivated_at,
        createdAt=subscription.created_at,
        updatedAt=subscription.updated_at,
    )


def _company_response(company) -> TenantCompanyResponse:
    return TenantCompanyResponse(
        id=company.id,
        tenantId=company.tenant_id,
        legalName=company.legal_name,
        tradeName=company.trade_name,
        taxId=company.tax_id,
        billingEmail=company.billing_email,
        billingPhone=company.billing_phone,
        addressLine1=company.address_line1,
        addressLine2=company.address_line2,
        city=company.city,
        state=company.state,
        zipCode=company.zip_code,
        country=company.country,
        isActive=company.is_active,
        createdAt=company.created_at,
        updatedAt=company.updated_at,
    )


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        tenantId=str(user.tenant_id),
        email=user.email,
        fullName=user.full_name,
        roles=user.roles or [],
        isActive=user.is_active,
        isSuspended=getattr(user, "is_suspended", False),
        isSuperuser=user.is_superuser,
        createdAt=user.created_at,
        updatedAt=user.updated_at,
    )


@router.get(
    "/admin/plans",
    response_model=list[CommercialPlanResponse],
)
def list_plans(
    request: Request,
    service: ServiceDependency,
    include_inactive: bool = Query(False),
    current_user: CurrentUser = Depends(require_roles(SUPERADMIN_ROLE)),
) -> list[CommercialPlanResponse]:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        plans = service.list_commercial_plans(acting, include_inactive=include_inactive)
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    responses = [_plan_response(plan) for plan in plans]
    _audit_collection(request, resource_type="commercial_plan", count=len(responses))
    return responses


@router.get(
    "/admin/plans/{plan_id}",
    response_model=CommercialPlanResponse,
)
def get_plan(
    request: Request,
    plan_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    current_user: CurrentUser = Depends(require_roles(SUPERADMIN_ROLE)),
) -> CommercialPlanResponse:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        plan = service.get_commercial_plan(acting, UUID(plan_id))
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _plan_response(plan)
    _audit_entity(
        request, resource_type="commercial_plan", resource_id=plan.id, payload=response
    )
    return response


@router.patch(
    "/admin/plans/{plan_id}",
    response_model=CommercialPlanResponse,
)
def update_plan(
    request: Request,
    plan_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: PlanUpdateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(require_roles(SUPERADMIN_ROLE)),
) -> CommercialPlanResponse:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        plan = service.update_commercial_plan(
            acting,
            UUID(plan_id),
            PlanUpdateInput(
                name=payload.name,
                description=payload.description,
                max_users=payload.maxUsers,
                price_cents=payload.priceCents,
                currency=payload.currency,
                billing_cycle_months=payload.billingCycleMonths,
                is_active=payload.isActive,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _plan_response(plan)
    _audit_entity(
        request, resource_type="commercial_plan", resource_id=plan.id, payload=response
    )
    return response


@router.post(
    "/admin/plans",
    response_model=CommercialPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(
    request: Request,
    payload: PlanCreateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(require_roles(SUPERADMIN_ROLE)),
) -> CommercialPlanResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        plan = service.create_commercial_plan(
            acting_user,
            PlanCreateInput(
                name=payload.name,
                description=payload.description,
                max_users=payload.maxUsers,
                price_cents=payload.priceCents,
                currency=payload.currency,
                billing_cycle_months=payload.billingCycleMonths,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _plan_response(plan)
    _audit_entity(
        request, resource_type="commercial_plan", resource_id=plan.id, payload=response
    )
    return response


@router.get(
    "/t/{tenant_id}/admin/payment-plans",
    response_model=list[PaymentPlanTemplateResponse],
)
def list_payment_plan_templates(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    include_inactive: bool = Query(False),
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> list[PaymentPlanTemplateResponse]:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        templates = service.list_payment_plan_templates(
            acting, UUID(tenant_id), include_inactive=include_inactive
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    responses = [_payment_plan_template_response(template) for template in templates]
    _audit_collection(
        request, resource_type="payment_plan_template", count=len(responses)
    )
    return responses


@router.post(
    "/t/{tenant_id}/admin/payment-plans",
    response_model=PaymentPlanTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_plan_template(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: PaymentPlanTemplateCreateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> PaymentPlanTemplateResponse:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        template = service.create_payment_plan_template(
            acting,
            UUID(tenant_id),
            PaymentPlanTemplateCreateInput(
                product_code=payload.productCode,
                principal=payload.principal,
                discount_rate=payload.discountRate,
                name=payload.name,
                description=payload.description,
                metadata=payload.metadata,
                is_active=payload.isActive,
                installments=[
                    PaymentPlanInstallmentInput(period=item.period, amount=item.amount)
                    for item in payload.installments
                ],
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _payment_plan_template_response(template)
    _audit_entity(
        request,
        resource_type="payment_plan_template",
        resource_id=template.id,
        payload=response,
    )
    return response


@router.patch(
    "/t/{tenant_id}/admin/payment-plans/{template_id}",
    response_model=PaymentPlanTemplateResponse,
)
def update_payment_plan_template(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    template_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: PaymentPlanTemplateUpdateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> PaymentPlanTemplateResponse:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    installments = None
    if payload.installments is not None:
        installments = [
            PaymentPlanInstallmentInput(period=item.period, amount=item.amount)
            for item in payload.installments
        ]
    try:
        template = service.update_payment_plan_template(
            acting,
            UUID(tenant_id),
            UUID(template_id),
            PaymentPlanTemplateUpdateInput(
                name=payload.name,
                description=payload.description,
                principal=payload.principal,
                discount_rate=payload.discountRate,
                metadata=payload.metadata,
                is_active=payload.isActive,
                installments=installments,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _payment_plan_template_response(template)
    _audit_entity(
        request,
        resource_type="payment_plan_template",
        resource_id=template.id,
        payload=response,
    )
    return response


@router.get(
    "/admin/tenants",
    response_model=list[TenantResponse],
)
def list_tenants(
    request: Request,
    service: ServiceDependency,
    include_inactive: bool = Query(False),
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> list[TenantResponse]:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        tenants = service.list_tenants(acting, include_inactive=include_inactive)
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    responses = [_tenant_response(tenant) for tenant in tenants]
    _audit_collection(request, resource_type="tenant", count=len(responses))
    return responses


@router.get(
    "/admin/tenants/{tenant_id}",
    response_model=TenantResponse,
)
def get_tenant(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> TenantResponse:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        tenant = service.get_tenant(acting, UUID(tenant_id))
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _tenant_response(tenant)
    _audit_entity(
        request, resource_type="tenant", resource_id=tenant.id, payload=response
    )
    return response


@router.post(
    "/admin/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant(
    request: Request,
    payload: TenantCreateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(require_roles(SUPERADMIN_ROLE)),
) -> TenantResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        tenant = service.create_tenant(
            acting_user,
            TenantCreateInput(
                name=payload.name,
                slug=payload.slug,
                companies=_map_companies(payload),
                administrators=_map_admins(payload),
                metadata=payload.metadata,
                plan_id=payload.planId,
                is_default=payload.isDefault,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _tenant_response(tenant)
    _audit_entity(
        request, resource_type="tenant", resource_id=tenant.id, payload=response
    )
    return response


@router.post(
    "/admin/tenants/{tenant_id}/assign-plan",
    response_model=TenantPlanSubscriptionResponse,
    status_code=status.HTTP_200_OK,
)
def assign_plan(
    request: Request,
    payload: PlanAssignRequest,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    current_user: CurrentUser = Depends(require_roles(SUPERADMIN_ROLE)),
) -> TenantPlanSubscriptionResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        subscription = service.assign_plan_to_tenant(
            acting_user, UUID(tenant_id), payload.planId
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _subscription_response(subscription)
    _audit_entity(
        request,
        resource_type="tenant_plan_subscription",
        resource_id=subscription.id,
        payload=response,
    )
    return response


@router.post(
    "/admin/tenants/{tenant_id}/companies",
    response_model=list[TenantCompanyResponse],
    status_code=status.HTTP_201_CREATED,
)
def attach_companies(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: TenantCompaniesAttachRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> list[TenantCompanyResponse]:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    companies_input = [
        CompanyInput(
            legal_name=company.legalName,
            trade_name=company.tradeName,
            tax_id=company.taxId,
            billing_email=str(company.billingEmail),
            billing_phone=company.billingPhone,
            address_line1=company.addressLine1,
            address_line2=company.addressLine2,
            city=company.city,
            state=company.state,
            zip_code=company.zipCode,
            country=company.country,
        )
        for company in payload.companies
    ]
    try:
        created = service.attach_companies_to_tenant(
            acting, UUID(tenant_id), companies_input
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    responses = [_company_response(company) for company in created]
    _audit_entity(
        request,
        resource_type="tenant_companies",
        resource_id=f"attach:{tenant_id}",
        payload={"count": len(responses)},
    )
    return responses


@router.get(
    "/admin/tenants/{tenant_id}/companies",
    response_model=list[TenantCompanyResponse],
)
def list_companies(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    include_inactive: bool = Query(False),
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> list[TenantCompanyResponse]:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        companies = service.list_tenant_companies(
            acting, UUID(tenant_id), include_inactive=include_inactive
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    responses = [_company_response(company) for company in companies]
    _audit_collection(request, resource_type="tenant_companies", count=len(responses))
    return responses


@router.patch(
    "/admin/companies/{company_id}",
    response_model=TenantCompanyResponse,
)
def update_company(
    request: Request,
    company_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: CompanyUpdateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> TenantCompanyResponse:
    _set_audit_actor(request, current_user)
    acting = _acting_user(current_user)
    try:
        company = service.update_company(
            acting,
            UUID(company_id),
            CompanyUpdateInput(
                legal_name=payload.legalName,
                trade_name=payload.tradeName,
                tax_id=payload.taxId,
                billing_email=(
                    str(payload.billingEmail) if payload.billingEmail else None
                ),
                billing_phone=payload.billingPhone,
                address_line1=payload.addressLine1,
                address_line2=payload.addressLine2,
                city=payload.city,
                state=payload.state,
                zip_code=payload.zipCode,
                country=payload.country,
                is_active=payload.isActive,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _company_response(company)
    _audit_entity(
        request,
        resource_type="tenant_company",
        resource_id=company.id,
        payload=response,
    )
    return response


@router.post(
    "/t/{tenant_id}/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: UserCreate,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> UserResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        user = service.create_user(
            acting_user,
            UUID(tenant_id),
            UserInput(
                email=payload.email,
                password=payload.password,
                full_name=payload.fullName,
                roles=payload.roles,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _user_response(user)
    _audit_entity(request, resource_type="user", resource_id=user.id, payload=response)
    return response


@router.get(
    "/t/{tenant_id}/admin/users",
    response_model=list[UserResponse],
)
def list_users(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    include_inactive: bool = Query(False),
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> list[UserResponse]:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        users = service.list_users(
            acting_user, UUID(tenant_id), include_inactive=include_inactive
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    responses = [_user_response(user) for user in users]
    _audit_collection(request, resource_type="user", count=len(responses))
    return responses


@router.get(
    "/t/{tenant_id}/admin/users/{user_id}",
    response_model=UserResponse,
)
def get_user(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    user_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> UserResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        user = service.get_user(acting_user, UUID(user_id))
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _user_response(user)
    _audit_entity(request, resource_type="user", resource_id=user.id, payload=response)
    return response


@router.patch(
    "/t/{tenant_id}/admin/users/{user_id}",
    response_model=UserResponse,
)
def update_user(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    user_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: UserUpdateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> UserResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        user = service.update_user(
            acting_user,
            UUID(user_id),
            UserUpdateInput(
                full_name=payload.fullName,
                password=payload.password,
                is_active=payload.isActive,
                roles=payload.roles,
            ),
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _user_response(user)
    _audit_entity(request, resource_type="user", resource_id=user.id, payload=response)
    return response


@router.post(
    "/t/{tenant_id}/admin/users/{user_id}/suspend",
    response_model=UserResponse,
)
def suspend_user(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    user_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: UserSuspendRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> UserResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        user = service.suspend_user(acting_user, UUID(user_id), reason=payload.reason)
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _user_response(user)
    _audit_entity(
        request, resource_type="user_suspension", resource_id=user.id, payload=response
    )
    return response


@router.post(
    "/t/{tenant_id}/admin/users/{user_id}/reinstate",
    response_model=UserResponse,
)
def reinstate_user(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    user_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: UserReinstateRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> UserResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        user = service.reinstate_user(
            acting_user, UUID(user_id), reactivate=payload.reactivate
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _user_response(user)
    _audit_entity(
        request,
        resource_type="user_reinstatement",
        resource_id=user.id,
        payload=response,
    )
    return response


@router.post(
    "/t/{tenant_id}/admin/users/{user_id}/reset-password",
    response_model=PasswordResetResponse,
)
def initiate_password_reset(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    user_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> PasswordResetResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        token = service.initiate_password_reset(acting_user, UUID(user_id))
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = PasswordResetResponse(token=token.token, expiresAt=token.expires_at)
    _audit_entity(
        request,
        resource_type="user_password_reset_request",
        resource_id=user_id,
        payload={"expiresAt": token.expires_at.isoformat()},
    )
    return response


@router.post(
    "/t/{tenant_id}/admin/users/{user_id}/reset-password/confirm",
    response_model=UserResponse,
)
def confirm_password_reset(
    request: Request,
    tenant_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    user_id: Annotated[str, Path(pattern=r"^[0-9a-fA-F-]{36}$")],
    payload: PasswordResetConfirmRequest,
    service: ServiceDependency,
    current_user: CurrentUser = Depends(
        require_roles(SUPERADMIN_ROLE, TENANT_ADMIN_ROLE)
    ),
) -> UserResponse:
    _set_audit_actor(request, current_user)
    acting_user = _acting_user(current_user)
    try:
        user = service.complete_password_reset(
            acting_user, UUID(user_id), payload.token, payload.newPassword
        )
    except Exception as exc:  # pragma: no cover - thin mapping
        _handle_service_error(exc)
    response = _user_response(user)
    _audit_entity(
        request,
        resource_type="user_password_reset_confirm",
        resource_id=user.id,
        payload=response,
    )
    return response
