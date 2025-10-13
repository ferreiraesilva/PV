from __future__ import annotations

import secrets
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.roles import (
    ALLOWED_ROLES,
    SUPERADMIN_ROLE,
    TENANT_ADMIN_ROLE,
    TENANT_USER_ROLE,
)
from app.core.security import get_password_hash, verify_password
from app.db.models import (
    CommercialPlan,
    FinancialSettings,
    PaymentPlanInstallment,
    PaymentPlanTemplate,
    Tenant,
    TenantCompany,
    TenantPlanSubscription,
    User,
)


class AdministrationError(Exception):
    """Base class for administration related errors."""


class PermissionDeniedError(AdministrationError):
    """Raised when the acting user does not have the required role."""


class NotFoundError(AdministrationError):
    """Raised when an entity cannot be located."""


class BusinessRuleViolation(AdministrationError):
    """Raised when a domain rule is violated."""


@dataclass(frozen=True)
class ActingUser:
    id: UUID
    tenant_id: UUID
    roles: frozenset[str]

    def has_any_role(self, *roles: str) -> bool:
        return bool(
            self._normalized_roles().intersection(self._normalize_role_set(roles))
        )

    def is_superuser(self) -> bool:
        """Return True when the acting user holds the superadmin role."""
        return self.has_any_role(SUPERADMIN_ROLE, "superuser")

    def is_tenant_admin_for(self, tenant_id: UUID) -> bool:
        """Return True when the user is tenant admin for the provided tenant."""
        return (
            self.has_any_role(TENANT_ADMIN_ROLE, "tenant_admin")
            and self.tenant_id == tenant_id
        )

    def _normalized_roles(self) -> set[str]:
        return {self._normalize_token(role) for role in self.roles}

    @staticmethod
    def _normalize_role_set(values: Sequence[str]) -> set[str]:
        return {ActingUser._normalize_token(value) for value in values}

    @staticmethod
    def _normalize_token(value: str) -> str:
        token = value.replace("-", "").replace("_", "").strip().lower()
        if token in {"superuser", "superadministrator", "superadmin"}:
            return SUPERADMIN_ROLE
        if token in {"tenantadmin", "tenantadministrator"}:
            return TENANT_ADMIN_ROLE
        if token in {"tenantuser", "enduser"}:
            return TENANT_USER_ROLE
        return token


@dataclass(frozen=True)
class CompanyInput:
    legal_name: str
    tax_id: str
    billing_email: str
    address_line1: str
    city: str
    state: str
    zip_code: str
    country: str = "BR"
    trade_name: str | None = None
    billing_phone: str | None = None
    address_line2: str | None = None


@dataclass(frozen=True)
class CompanyUpdateInput:
    legal_name: str | None = None
    trade_name: str | None = None
    tax_id: str | None = None
    billing_email: str | None = None
    billing_phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class UserInput:
    email: str
    password: str
    full_name: str | None = None
    roles: Sequence[str] | None = None


@dataclass(frozen=True)
class TenantCreateInput:
    name: str
    slug: str
    companies: Sequence[CompanyInput]
    administrators: Sequence[UserInput]
    metadata: dict | None = None
    plan_id: UUID | None = None
    is_default: bool = False


@dataclass(frozen=True)
class PlanCreateInput:
    name: str
    description: str | None = None
    max_users: int | None = None
    price_cents: int | None = None
    currency: str = "BRL"
    billing_cycle_months: int = 1


@dataclass(frozen=True)
class PlanUpdateInput:
    name: str | None = None
    description: str | None = None
    max_users: int | None = None
    price_cents: int | None = None
    currency: str | None = None
    billing_cycle_months: int | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class PaymentPlanInstallmentInput:
    period: int
    amount: float


@dataclass(frozen=True)
class PaymentPlanTemplateCreateInput:
    product_code: str
    principal: float
    discount_rate: float
    installments: Sequence[PaymentPlanInstallmentInput]
    name: str | None = None
    description: str | None = None
    metadata: dict | None = None
    is_active: bool = True


@dataclass(frozen=True)
class PaymentPlanTemplateUpdateInput:
    name: str | None = None
    description: str | None = None
    principal: float | None = None
    discount_rate: float | None = None
    installments: Sequence[PaymentPlanInstallmentInput] | None = None
    metadata: dict | None = None
    is_active: bool | None = None


@dataclass(frozen=True)
class UserUpdateInput:
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    roles: Sequence[str] | None = None


@dataclass(frozen=True)
class PasswordResetToken:
    token: str
    expires_at: datetime


class AdministrationService:
    def __init__(
        self,
        session: Session | None = None,
        *,
        repository: object | None = None,
        db: object | None = None,
    ) -> None:
        if repository is None and db is not None:
            repository = db

        if session is None and isinstance(repository, Session):
            session = repository  # repository actually a session
            repository = None

        self.session = session
        self._repository = repository

    # --------- Tenant management ---------
    def list_tenants(
        self, acting_user: ActingUser, *, include_inactive: bool = False
    ) -> list[Tenant]:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        stmt = select(Tenant)
        if not include_inactive:
            stmt = stmt.where(Tenant.is_active.is_(True))
        if SUPERADMIN_ROLE not in acting_user.roles:
            stmt = stmt.where(Tenant.id == acting_user.tenant_id)
        stmt = stmt.order_by(Tenant.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_tenant(self, acting_user: ActingUser, tenant_id: UUID) -> Tenant:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        tenant = self._get_tenant(tenant_id)
        self._assert_tenant_scope(acting_user, tenant.id)
        return tenant

    def create_tenant(
        self, acting_user: ActingUser, payload: TenantCreateInput
    ) -> Tenant:
        if not acting_user.is_superuser():
            raise PermissionDeniedError("Only superusers can create new tenants")
        self._require_roles(acting_user, {SUPERADMIN_ROLE})

        if self._repository is not None:
            if getattr(
                self._repository, "find_tenant_by_slug", None
            ) and self._repository.find_tenant_by_slug(payload.slug):
                raise BusinessRuleViolation(
                    f"Tenant slug '{payload.slug}' is already in use"
                )
            creator = getattr(self._repository, "create_tenant", None)
            if creator is None:
                raise NotImplementedError("Repository does not implement create_tenant")
            return creator(payload, acting_user=acting_user)

        if not payload.companies:
            raise BusinessRuleViolation("Tenant must include at least one company")
        if not payload.administrators:
            raise BusinessRuleViolation(
                "Tenant must include at least one administrator"
            )
        normalized_admin_roles = [
            self._normalize_roles(admin.roles) for admin in payload.administrators
        ]
        if not any(TENANT_ADMIN_ROLE in roles for roles in normalized_admin_roles):
            raise BusinessRuleViolation(
                "At least one administrator must hold the tenantadmin role"
            )
        if payload.is_default and self._default_tenant_exists():
            raise BusinessRuleViolation("Default tenant already configured")

        tenant = Tenant(
            name=payload.name,
            slug=payload.slug,
            is_active=True,
            is_default=payload.is_default,
            metadata_json=payload.metadata,
        )

        try:
            self.session.add(tenant)
            self.session.flush()

            for company in payload.companies:
                self.session.add(
                    TenantCompany(
                        tenant_id=tenant.id,
                        legal_name=company.legal_name,
                        trade_name=company.trade_name,
                        tax_id=company.tax_id,
                        billing_email=self._normalize_email(company.billing_email),
                        billing_phone=company.billing_phone,
                        address_line1=company.address_line1,
                        address_line2=company.address_line2,
                        city=company.city,
                        state=company.state,
                        zip_code=company.zip_code,
                        country=company.country,
                    )
                )

            for admin_input, roles in zip(
                payload.administrators, normalized_admin_roles
            ):
                self.session.add(
                    User(
                        tenant_id=tenant.id,
                        email=self._normalize_email(admin_input.email),
                        hashed_password=get_password_hash(admin_input.password),
                        full_name=admin_input.full_name,
                        roles=roles,
                        is_active=True,
                        is_superuser=SUPERADMIN_ROLE in roles,
                    )
                )

            if payload.plan_id:
                self._assign_plan(tenant.id, payload.plan_id)

            self._commit()
        except (
            IntegrityError
        ) as exc:  # pragma: no cover - defensive guard for DB validations
            self.session.rollback()
            raise BusinessRuleViolation(
                "Tenant data violates uniqueness constraints"
            ) from exc

        self.session.refresh(tenant)
        return tenant

    def attach_companies_to_tenant(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        companies: Sequence[CompanyInput],
    ) -> list[TenantCompany]:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        self._assert_tenant_scope(acting_user, tenant_id)
        if not companies:
            return []
        if len({company.tax_id for company in companies}) != len(companies):
            raise BusinessRuleViolation(
                "Duplicate tax ids provided in companies payload"
            )

        self._get_tenant(tenant_id)
        persisted: list[TenantCompany] = []
        for company in companies:
            entity = TenantCompany(
                tenant_id=tenant_id,
                legal_name=company.legal_name,
                trade_name=company.trade_name,
                tax_id=company.tax_id,
                billing_email=self._normalize_email(company.billing_email),
                billing_phone=company.billing_phone,
                address_line1=company.address_line1,
                address_line2=company.address_line2,
                city=company.city,
                state=company.state,
                zip_code=company.zip_code,
                country=company.country,
            )
            self.session.add(entity)
            persisted.append(entity)

        try:
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation(
                "Company data violates uniqueness constraints"
            ) from exc

        for entity in persisted:
            self.session.refresh(entity)
        return persisted

    def list_tenant_companies(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        *,
        include_inactive: bool = False,
    ) -> list[TenantCompany]:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        self._assert_tenant_scope(acting_user, tenant_id)
        stmt = select(TenantCompany).where(TenantCompany.tenant_id == tenant_id)
        if not include_inactive:
            stmt = stmt.where(TenantCompany.is_active.is_(True))
        stmt = stmt.order_by(TenantCompany.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_company(self, acting_user: ActingUser, company_id: UUID) -> TenantCompany:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        company = self._get_company(company_id)
        self._assert_tenant_scope(acting_user, company.tenant_id)
        return company

    def update_company(
        self,
        acting_user: ActingUser,
        company_id: UUID,
        payload: CompanyUpdateInput,
    ) -> TenantCompany:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        company = self._get_company(company_id)
        self._assert_tenant_scope(acting_user, company.tenant_id)

        if payload.legal_name is not None:
            company.legal_name = payload.legal_name
        if payload.trade_name is not None:
            company.trade_name = payload.trade_name
        if payload.tax_id is not None:
            company.tax_id = payload.tax_id
        if payload.billing_email is not None:
            company.billing_email = self._normalize_email(payload.billing_email)
        if payload.billing_phone is not None:
            company.billing_phone = payload.billing_phone
        if payload.address_line1 is not None:
            company.address_line1 = payload.address_line1
        if payload.address_line2 is not None:
            company.address_line2 = payload.address_line2
        if payload.city is not None:
            company.city = payload.city
        if payload.state is not None:
            company.state = payload.state
        if payload.zip_code is not None:
            company.zip_code = payload.zip_code
        if payload.country is not None:
            company.country = payload.country
        if payload.is_active is not None:
            company.is_active = payload.is_active

        try:
            self.session.add(company)
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation(
                "Company update violates database constraints"
            ) from exc

        self.session.refresh(company)
        return company

    # --------- Financial settings ---------
    def update_financial_settings(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        updates: dict[str, Any],
    ) -> FinancialSettings:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        if not updates:
            raise BusinessRuleViolation("No financial settings fields provided")

        tenant = self._get_tenant(tenant_id)
        self._assert_tenant_scope(acting_user, tenant.id)

        allowed_fields = {
            "periods_per_year",
            "default_multiplier",
            "cancellation_multiplier",
        }
        unknown = set(updates).difference(allowed_fields)
        if unknown:
            raise BusinessRuleViolation(
                f"Unknown financial settings fields: {sorted(unknown)}"
            )

        normalized: dict[str, Any] = {}
        if "periods_per_year" in updates:
            value = updates["periods_per_year"]
            if value is None:
                normalized["periods_per_year"] = None
            else:
                if not isinstance(value, int):
                    raise BusinessRuleViolation(
                        "periods_per_year must be an integer value"
                    )
                if value < 1:
                    raise BusinessRuleViolation(
                        "periods_per_year must be greater than zero"
                    )
                normalized["periods_per_year"] = value

        for field_name in ("default_multiplier", "cancellation_multiplier"):
            if field_name not in updates:
                continue
            value = updates[field_name]
            if value is None:
                normalized[field_name] = None
                continue
            try:
                decimal_value = self._to_decimal(value)
            except (ArithmeticError, ValueError, TypeError):
                raise BusinessRuleViolation(
                    f"{field_name.replace('_', ' ')} must be a numeric value"
                ) from None
            if decimal_value < Decimal("0"):
                raise BusinessRuleViolation(
                    f"{field_name.replace('_', ' ')} must be greater than or equal to zero"
                )
            normalized[field_name] = decimal_value

        if not normalized:
            raise BusinessRuleViolation("No financial settings fields provided")

        settings = tenant.financial_settings
        if settings is None:
            settings = FinancialSettings(tenant_id=tenant.id)
            tenant.financial_settings = settings
            self.session.add(settings)

        for attr, value in normalized.items():
            setattr(settings, attr, value)

        try:
            self.session.add(settings)
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation(
                "Financial settings update violates database constraints"
            ) from exc

        self.session.refresh(settings)
        return settings

    # --------- Plan management ---------
    def create_commercial_plan(
        self, acting_user: ActingUser, payload: PlanCreateInput
    ) -> CommercialPlan:
        self._require_roles(acting_user, {SUPERADMIN_ROLE})
        if payload.max_users is not None and payload.max_users < 1:
            raise BusinessRuleViolation("Plan max_users must be positive")
        if payload.billing_cycle_months < 1:
            raise BusinessRuleViolation("billing_cycle_months must be at least 1")

        owner = self._get_default_tenant()
        plan = CommercialPlan(
            tenant_id=owner.id,
            name=payload.name,
            description=payload.description,
            max_users=payload.max_users,
            price_cents=payload.price_cents,
            currency=payload.currency,
            billing_cycle_months=payload.billing_cycle_months,
            is_active=True,
        )

        try:
            self.session.add(plan)
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation(
                "Plan already exists with the same name"
            ) from exc

        self.session.refresh(plan)
        return plan

    def list_commercial_plans(
        self,
        acting_user: ActingUser,
        *,
        include_inactive: bool = False,
    ) -> list[CommercialPlan]:
        self._require_roles(acting_user, {SUPERADMIN_ROLE})
        owner = self._get_default_tenant()
        stmt = select(CommercialPlan).where(CommercialPlan.tenant_id == owner.id)
        if not include_inactive:
            stmt = stmt.where(CommercialPlan.is_active.is_(True))
        stmt = stmt.order_by(CommercialPlan.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_commercial_plan(
        self, acting_user: ActingUser, plan_id: UUID
    ) -> CommercialPlan:
        self._require_roles(acting_user, {SUPERADMIN_ROLE})
        return self._get_plan(plan_id, allow_inactive=True)

    def update_commercial_plan(
        self,
        acting_user: ActingUser,
        plan_id: UUID,
        payload: PlanUpdateInput,
    ) -> CommercialPlan:
        self._require_roles(acting_user, {SUPERADMIN_ROLE})
        plan = self._get_plan(plan_id, allow_inactive=True)

        if payload.name is not None:
            plan.name = payload.name
        if payload.description is not None:
            plan.description = payload.description
        if payload.max_users is not None:
            if payload.max_users < 1:
                raise BusinessRuleViolation("Plan max_users must be positive")
            plan.max_users = payload.max_users
        if payload.price_cents is not None:
            plan.price_cents = payload.price_cents
        if payload.currency is not None:
            plan.currency = payload.currency
        if payload.billing_cycle_months is not None:
            if payload.billing_cycle_months < 1:
                raise BusinessRuleViolation("billing_cycle_months must be at least 1")
            plan.billing_cycle_months = payload.billing_cycle_months
        if payload.is_active is not None:
            plan.is_active = payload.is_active

        try:
            self.session.add(plan)
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation(
                "Plan update violates database constraints"
            ) from exc

        self.session.refresh(plan)
        return plan

    def assign_plan_to_tenant(
        self, acting_user: ActingUser, tenant_id: UUID, plan_id: UUID
    ) -> TenantPlanSubscription:
        self._require_roles(acting_user, {SUPERADMIN_ROLE})
        subscription = self._assign_plan(tenant_id, plan_id)
        self._commit()
        self.session.refresh(subscription)
        return subscription

    # --------- Payment plan templates ---------
    def list_payment_plan_templates(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        *,
        include_inactive: bool = False,
    ) -> list[PaymentPlanTemplate]:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        self._assert_tenant_scope(acting_user, tenant_id)
        stmt = select(PaymentPlanTemplate).where(
            PaymentPlanTemplate.tenant_id == tenant_id
        )
        if not include_inactive:
            stmt = stmt.where(PaymentPlanTemplate.is_active.is_(True))
        stmt = stmt.order_by(PaymentPlanTemplate.product_code)
        result = self.session.execute(stmt).unique()
        return list(result.scalars())

    def create_payment_plan_template(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        payload: PaymentPlanTemplateCreateInput,
    ) -> PaymentPlanTemplate:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        self._assert_tenant_scope(acting_user, tenant_id)
        product_code = self._normalize_product_code(payload.product_code)
        self._validate_payment_plan_values(payload.principal, payload.discount_rate)
        installments = self._validate_payment_plan_installments(payload.installments)
        stmt = select(PaymentPlanTemplate).where(
            PaymentPlanTemplate.tenant_id == tenant_id,
            func.lower(PaymentPlanTemplate.product_code) == product_code.lower(),
        )
        existing = self.session.execute(stmt).scalar_one_or_none()
        if existing is not None:
            raise BusinessRuleViolation("Product code already in use for this tenant")
        template = PaymentPlanTemplate(
            tenant_id=tenant_id,
            product_code=product_code,
            name=payload.name,
            description=payload.description,
            principal=self._to_decimal(payload.principal),
            discount_rate=self._to_decimal(payload.discount_rate),
            metadata_json=payload.metadata,
            is_active=payload.is_active,
        )
        template.installments = [
            PaymentPlanInstallment(
                period=item.period, amount=self._to_decimal(item.amount)
            )
            for item in installments
        ]
        self.session.add(template)
        self._commit()
        self.session.refresh(template)
        return template

    def update_payment_plan_template(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        template_id: UUID,
        payload: PaymentPlanTemplateUpdateInput,
    ) -> PaymentPlanTemplate:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        template = self._get_payment_plan_template(template_id)
        self._assert_tenant_scope(acting_user, template.tenant_id)
        if template.tenant_id != tenant_id:
            raise PermissionDeniedError(
                "Template does not belong to the requested tenant"
            )
        if payload.name is not None:
            template.name = payload.name
        if payload.description is not None:
            template.description = payload.description
        if payload.principal is not None:
            self._validate_payment_plan_values(
                payload.principal, template.discount_rate
            )
            template.principal = self._to_decimal(payload.principal)
        if payload.discount_rate is not None:
            self._validate_payment_plan_values(
                template.principal, payload.discount_rate
            )
            template.discount_rate = self._to_decimal(payload.discount_rate)
        if payload.metadata is not None:
            template.metadata_json = payload.metadata
        if payload.is_active is not None:
            template.is_active = payload.is_active

        if payload.installments is not None:
            installments = self._validate_payment_plan_installments(
                payload.installments
            )
            self.session.add(template)
            self.session.flush()
            dialect_name = getattr(
                getattr(self.session.bind, "dialect", None), "name", None
            )
            identifier = (
                template.id.hex if dialect_name == "sqlite" else str(template.id)
            )
            self.session.execute(
                text(
                    "DELETE FROM payment_plan_installments WHERE template_id = :template_id"
                ),
                {"template_id": identifier},
            )
            self._commit()
            for item in installments:
                self.session.add(
                    PaymentPlanInstallment(
                        template_id=template.id,
                        period=item.period,
                        amount=self._to_decimal(item.amount),
                    )
                )
            self._commit()
            return self._get_payment_plan_template(template_id)

        self.session.add(template)
        self._commit()
        self.session.refresh(template)
        return template

    # --------- User management ---------
    def create_user(
        self, acting_user: ActingUser, tenant_id: UUID, payload: UserInput
    ) -> User:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        if self._repository is not None:
            if not (
                acting_user.is_superuser() or acting_user.is_tenant_admin_for(tenant_id)
            ):
                raise PermissionDeniedError(
                    "Tenant administrators can only manage their own tenant"
                )
            get_tenant = getattr(self._repository, "get_tenant", None)
            tenant = get_tenant(tenant_id) if callable(get_tenant) else None
            if tenant is None:
                raise NotFoundError(f"Tenant with ID '{tenant_id}' not found")
            finder = getattr(self._repository, "find_user_by_email", None)
            if callable(finder) and finder(tenant_id, payload.email):
                raise BusinessRuleViolation(
                    f"User with email '{payload.email}' already exists"
                )
            creator = getattr(self._repository, "create_user", None)
            if creator is None:
                raise NotImplementedError("Repository does not implement create_user")
            return creator(tenant_id, payload, acting_user=acting_user)

        self._assert_tenant_scope(acting_user, tenant_id)
        tenant = self._get_tenant(tenant_id)

        roles = self._normalize_roles(payload.roles)
        self._assert_role_assignment(acting_user, roles)
        self._ensure_user_limit(tenant, additional_users=1)

        user = User(
            tenant_id=tenant.id,
            email=self._normalize_email(payload.email),
            hashed_password=get_password_hash(payload.password),
            full_name=payload.full_name,
            roles=roles,
            is_active=True,
            is_superuser=SUPERADMIN_ROLE in roles,
        )

        try:
            self.session.add(user)
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation("Email already in use for this tenant") from exc

        self.session.refresh(user)
        return user

    def list_users(
        self,
        acting_user: ActingUser,
        tenant_id: UUID,
        *,
        include_inactive: bool = False,
    ) -> list[User]:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        self._assert_tenant_scope(acting_user, tenant_id)
        stmt = select(User).where(User.tenant_id == tenant_id)
        if not include_inactive:
            stmt = stmt.where(User.is_active.is_(True), User.is_suspended.is_(False))
        stmt = stmt.order_by(User.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_user(self, acting_user: ActingUser, user_id: UUID) -> User:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        if self._repository is not None:
            getter = getattr(self._repository, "get_user", None)
            if getter is None:
                raise NotImplementedError("Repository does not implement get_user")
            user = getter(user_id)
            if user is None:
                raise NotFoundError(f"User with ID '{user_id}' not found")
            if (
                not acting_user.is_superuser()
                and getattr(user, "tenant_id", None) != acting_user.tenant_id
            ):
                raise PermissionDeniedError(
                    "Insufficient permissions to access this user"
                )
            return user
        user = self._get_user(user_id)
        self._assert_tenant_scope(acting_user, user.tenant_id)
        return user

    def update_user(
        self, acting_user: ActingUser, user_id: UUID, payload: UserUpdateInput
    ) -> User:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        user = self._get_user(user_id)
        self._assert_tenant_scope(acting_user, user.tenant_id)

        tenant = self._get_tenant(user.tenant_id)
        original_roles = set(user.roles or [])
        target_roles = original_roles
        if payload.roles is not None:
            target_roles = set(self._normalize_roles(payload.roles))
            self._assert_role_assignment(acting_user, target_roles)

        if payload.password:
            user.hashed_password = get_password_hash(payload.password)
            self._clear_password_reset(user)
        if payload.full_name is not None:
            user.full_name = payload.full_name

        if payload.is_active is not None and payload.is_active != user.is_active:
            if payload.is_active and user.is_suspended:
                raise BusinessRuleViolation(
                    "Cannot activate a suspended user. Reinstate the account first"
                )
            if payload.is_active:
                self._ensure_user_limit(tenant, additional_users=1)
            else:
                if (
                    TENANT_ADMIN_ROLE in original_roles
                    and self._count_active_admins(
                        user.tenant_id, exclude_user_id=user.id
                    )
                    == 0
                ):
                    raise BusinessRuleViolation(
                        "Tenant must retain at least one active tenant administrator"
                    )
            user.is_active = payload.is_active

        if payload.roles is not None:
            if (
                TENANT_ADMIN_ROLE in original_roles
                and TENANT_ADMIN_ROLE not in target_roles
            ):
                if (
                    self._count_active_admins(user.tenant_id, exclude_user_id=user.id)
                    == 0
                ):
                    raise BusinessRuleViolation(
                        "Tenant must retain at least one active tenant administrator"
                    )
            user.roles = sorted(target_roles)
            user.is_superuser = SUPERADMIN_ROLE in target_roles

        try:
            self.session.add(user)
            self._commit()
        except IntegrityError as exc:  # pragma: no cover - database guard
            self.session.rollback()
            raise BusinessRuleViolation(
                "User update violates database constraints"
            ) from exc

        self.session.refresh(user)
        return user

    def suspend_user(
        self, acting_user: ActingUser, user_id: UUID, reason: str | None = None
    ) -> User:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        if self._repository is not None:
            if acting_user.id == user_id:
                raise BusinessRuleViolation("Users cannot suspend their own account")
            getter = getattr(self._repository, "get_user", None)
            if getter is None:
                raise NotImplementedError("Repository does not implement get_user")
            user = getter(user_id)
            if user is None:
                raise NotFoundError(f"User with ID '{user_id}' not found")
            suspender = getattr(self._repository, "suspend_user", None)
            if suspender is None:
                raise NotImplementedError("Repository does not implement suspend_user")
            return suspender(user_id, reason=reason, acting_user=acting_user)
        user = self._get_user(user_id)
        self._assert_tenant_scope(acting_user, user.tenant_id)
        if user.is_suspended:
            raise BusinessRuleViolation("User is already suspended")
        if (
            TENANT_ADMIN_ROLE in (user.roles or [])
            and self._count_active_admins(user.tenant_id, exclude_user_id=user.id) == 0
        ):
            raise BusinessRuleViolation(
                "Tenant must retain at least one active tenant administrator"
            )

        user.is_suspended = True
        user.suspended_at = self._now()
        user.suspension_reason = reason
        if user.is_active:
            user.is_active = False
        self.session.add(user)
        self._commit()
        self.session.refresh(user)
        return user

    def reinstate_user(
        self,
        acting_user: ActingUser,
        user_id: UUID,
        *,
        reactivate: bool = False,
    ) -> User:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        user = self._get_user(user_id)
        self._assert_tenant_scope(acting_user, user.tenant_id)
        if not user.is_suspended:
            raise BusinessRuleViolation("User is not suspended")

        tenant = self._get_tenant(user.tenant_id)
        user.is_suspended = False
        user.suspended_at = None
        user.suspension_reason = None
        if reactivate and not user.is_active:
            self._ensure_user_limit(tenant, additional_users=1)
            user.is_active = True
        self.session.add(user)
        self._commit()
        self.session.refresh(user)
        return user

    def initiate_password_reset(
        self,
        acting_user: ActingUser,
        user_id: UUID,
        *,
        expires_in_minutes: int = 60,
    ) -> PasswordResetToken:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        user = self._get_user(user_id)
        self._assert_tenant_scope(acting_user, user.tenant_id)

        raw_token = secrets.token_urlsafe(32)
        expires_at = self._now() + timedelta(minutes=expires_in_minutes)
        user.password_reset_token_hash = get_password_hash(raw_token)
        user.password_reset_token_expires_at = expires_at
        user.password_reset_requested_at = self._now()

        self.session.add(user)
        self._commit()
        self.session.refresh(user)
        return PasswordResetToken(token=raw_token, expires_at=expires_at)

    def complete_password_reset(
        self,
        acting_user: ActingUser,
        user_id: UUID,
        token: str,
        new_password: str,
    ) -> User:
        self._require_roles(acting_user, {SUPERADMIN_ROLE, TENANT_ADMIN_ROLE})
        user = self._get_user(user_id)
        self._assert_tenant_scope(acting_user, user.tenant_id)

        if (
            not user.password_reset_token_hash
            or not user.password_reset_token_expires_at
        ):
            raise BusinessRuleViolation("No reset request found for this user")
        expires_at = user.password_reset_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < self._now():
            self._clear_password_reset(user)
            self.session.add(user)
            self._commit()
            raise BusinessRuleViolation("Reset token has expired")
        if not verify_password(token, user.password_reset_token_hash):
            raise BusinessRuleViolation("Invalid reset token")

        user.hashed_password = get_password_hash(new_password)
        self._clear_password_reset(user)
        self.session.add(user)
        self._commit()
        self.session.refresh(user)
        return user

    # --------- Helpers ---------
    def _require_roles(self, acting_user: ActingUser, allowed: set[str]) -> None:
        if not acting_user.has_any_role(*allowed):
            raise PermissionDeniedError("Insufficient permissions for this operation")

    def _normalize_roles(self, roles: Sequence[str] | None) -> list[str]:
        normalized = {role.strip().lower() for role in (roles or []) if role}
        normalized.add(TENANT_USER_ROLE)
        unknown = normalized.difference(ALLOWED_ROLES)
        if unknown:
            raise BusinessRuleViolation(f"Unknown roles requested: {sorted(unknown)}")
        return sorted(normalized)

    def _assert_role_assignment(
        self, acting_user: ActingUser, target_roles: Sequence[str] | set[str]
    ) -> None:
        target = set(target_roles)
        if SUPERADMIN_ROLE in target and SUPERADMIN_ROLE not in acting_user.roles:
            raise PermissionDeniedError(
                "Only super administrators can assign the superadm role"
            )

    def _assert_tenant_scope(self, acting_user: ActingUser, tenant_id: UUID) -> None:
        if (
            SUPERADMIN_ROLE not in acting_user.roles
            and acting_user.tenant_id != tenant_id
        ):
            raise PermissionDeniedError(
                "Tenant administrators can only manage resources within their tenant"
            )

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def _get_tenant(self, tenant_id: UUID) -> Tenant:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        tenant = self.session.execute(stmt).scalar_one_or_none()
        if tenant is None:
            raise NotFoundError("Tenant not found")
        return tenant

    def _get_default_tenant(self) -> Tenant:
        stmt = select(Tenant).where(Tenant.is_default.is_(True)).limit(1)
        tenant = self.session.execute(stmt).scalar_one_or_none()
        if tenant is None:
            raise BusinessRuleViolation("Default tenant is not configured")
        return tenant

    def _default_tenant_exists(self) -> bool:
        stmt = (
            select(func.count()).select_from(Tenant).where(Tenant.is_default.is_(True))
        )
        return bool(self.session.execute(stmt).scalar_one())

    def _get_payment_plan_template(self, template_id: UUID) -> PaymentPlanTemplate:
        stmt = select(PaymentPlanTemplate).where(PaymentPlanTemplate.id == template_id)
        template = self.session.execute(stmt).unique().scalar_one_or_none()
        if template is None:
            raise NotFoundError("Payment plan template not found")
        return template

    @staticmethod
    def _normalize_product_code(code: str) -> str:
        normalized = code.strip()
        if not normalized:
            raise BusinessRuleViolation("product_code is required")
        if len(normalized) > 128:
            raise BusinessRuleViolation("product_code must be at most 128 characters")
        return normalized

    def _validate_payment_plan_values(
        self, principal: float | Decimal, discount_rate: float | Decimal
    ) -> None:
        principal_value = self._to_decimal(principal)
        discount_value = self._to_decimal(discount_rate)
        if principal_value <= Decimal("0"):
            raise BusinessRuleViolation("principal must be greater than zero")
        if discount_value < Decimal("0"):
            raise BusinessRuleViolation("discount_rate must be zero or positive")

    def _validate_payment_plan_installments(
        self,
        installments: Sequence[PaymentPlanInstallmentInput],
    ) -> list[PaymentPlanInstallmentInput]:
        if not installments:
            raise BusinessRuleViolation(
                "Payment plan must include at least one installment"
            )
        seen: set[int] = set()
        validated: list[PaymentPlanInstallmentInput] = []
        for item in installments:
            if item.period < 1:
                raise BusinessRuleViolation("Installment period must be at least 1")
            if item.amount <= 0:
                raise BusinessRuleViolation(
                    "Installment amount must be greater than zero"
                )
            if item.period in seen:
                raise BusinessRuleViolation("Installment periods must be unique")
            seen.add(item.period)
            validated.append(item)
        validated.sort(key=lambda value: value.period)
        return validated

    @staticmethod
    def _to_decimal(value: float | Decimal | int) -> Decimal:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def _get_plan(
        self, plan_id: UUID, *, allow_inactive: bool = False
    ) -> CommercialPlan:
        stmt = select(CommercialPlan).where(CommercialPlan.id == plan_id)
        plan = self.session.execute(stmt).scalar_one_or_none()
        if plan is None:
            raise NotFoundError("Plan not found")
        owner = self._get_tenant(plan.tenant_id)
        if not owner.is_default:
            raise BusinessRuleViolation(
                "Commercial plans must belong to the default tenant"
            )
        if not allow_inactive and not plan.is_active:
            raise BusinessRuleViolation("Plan is not active")
        return plan

    def _get_company(self, company_id: UUID) -> TenantCompany:
        stmt = select(TenantCompany).where(TenantCompany.id == company_id)
        company = self.session.execute(stmt).scalar_one_or_none()
        if company is None:
            raise NotFoundError("Company not found")
        return company

    def _get_user(self, user_id: UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        user = self.session.execute(stmt).scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found")
        return user

    def _get_active_subscription(
        self, tenant_id: UUID
    ) -> TenantPlanSubscription | None:
        stmt = (
            select(TenantPlanSubscription)
            .where(
                TenantPlanSubscription.tenant_id == tenant_id,
                TenantPlanSubscription.is_active.is_(True),
            )
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def _assign_plan(self, tenant_id: UUID, plan_id: UUID) -> TenantPlanSubscription:
        tenant = self._get_tenant(tenant_id)
        plan = self._get_plan(plan_id)

        active = self._get_active_subscription(tenant.id)
        now = self._now()
        if active and active.plan_id == plan.id:
            return active
        if active:
            active.is_active = False
            active.deactivated_at = now
            self.session.add(active)

        subscription = TenantPlanSubscription(
            tenant_id=tenant.id,
            plan_id=plan.id,
            is_active=True,
            activated_at=now,
        )
        self.session.add(subscription)
        self.session.flush()
        return subscription

    def _ensure_user_limit(self, tenant: Tenant, *, additional_users: int) -> None:
        if tenant.is_default:
            return
        subscription = self._get_active_subscription(tenant.id)
        if subscription is None:
            raise BusinessRuleViolation(
                "Tenant does not have an active commercial plan"
            )
        plan = self._get_plan(subscription.plan_id)
        if plan.max_users is None:
            return
        active_users = self._count_active_users(tenant.id)
        if active_users + additional_users > plan.max_users:
            raise BusinessRuleViolation(
                "Tenant has reached the maximum number of active users for the current plan"
            )

    def _count_active_users(self, tenant_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(User.tenant_id == tenant_id, User.is_active.is_(True))
        )
        return int(self.session.execute(stmt).scalar_one())

    def _count_active_admins(
        self, tenant_id: UUID, *, exclude_user_id: UUID | None = None
    ) -> int:
        stmt = select(User).where(User.tenant_id == tenant_id, User.is_active.is_(True))
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)
        users = self.session.execute(stmt).scalars().all()
        return sum(1 for current in users if TENANT_ADMIN_ROLE in (current.roles or []))

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _clear_password_reset(self, user: User) -> None:
        user.password_reset_token_hash = None
        user.password_reset_token_expires_at = None
        user.password_reset_requested_at = None

    def _commit(self) -> None:
        try:
            self.session.commit()
        except Exception:  # pragma: no cover - defensive rollback
            self.session.rollback()
            raise
