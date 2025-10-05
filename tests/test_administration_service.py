import uuid
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.roles import SUPERADMIN_ROLE, TENANT_ADMIN_ROLE, TENANT_USER_ROLE
from app.core.security import verify_password
from app.db.base import Base
from app.db.models import CommercialPlan, Tenant, TenantCompany, TenantPlanSubscription, User
from app.services.administration import (
    ActingUser,
    AdministrationService,
    BusinessRuleViolation,
    CompanyInput,
    PlanCreateInput,
    PlanUpdateInput,
    TenantCreateInput,
    UserInput,
    UserUpdateInput,
)


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    tables = [
        Tenant.__table__,
        TenantCompany.__table__,
        CommercialPlan.__table__,
        TenantPlanSubscription.__table__,
        User.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSession()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()


@pytest.fixture()
def service(session: Session) -> AdministrationService:
    return AdministrationService(session)


@pytest.fixture()
def default_tenant(session: Session) -> Tenant:
    tenant = Tenant(name="Default", slug="default", is_active=True, is_default=True)
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def _company() -> CompanyInput:
    return CompanyInput(
        legal_name="ACME Ltd",
        tax_id=uuid.uuid4().hex[:14],
        billing_email="billing@acme.test",
        address_line1="Main Street 100",
        city="Sao Paulo",
        state="SP",
        zip_code="01000-000",
        country="BR",
    )


def _super_admin(default_tenant: Tenant) -> ActingUser:
    return ActingUser(id=uuid.uuid4(), tenant_id=default_tenant.id, roles=frozenset({SUPERADMIN_ROLE}))


@pytest.fixture()
def superadmin(default_tenant: Tenant) -> ActingUser:
    return _super_admin(default_tenant)


def test_create_tenant_requires_tenant_admin_role(service: AdministrationService, superadmin: ActingUser) -> None:
    tenant_input = TenantCreateInput(
        name="Client One",
        slug="client-one",
        companies=[_company()],
        administrators=[UserInput(email="owner@client.test", password="Secret123", roles=[TENANT_USER_ROLE])],
    )

    with pytest.raises(BusinessRuleViolation, match="tenantadmin role"):
        service.create_tenant(superadmin, tenant_input)


def test_create_user_respects_plan_limit(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    plan = service.create_commercial_plan(superadmin, PlanCreateInput(name="Starter", max_users=2))

    tenant_payload = TenantCreateInput(
        name="Client Two",
        slug="client-two",
        companies=[_company()],
        administrators=[
            UserInput(email="admin@client2.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
        ],
        plan_id=plan.id,
    )
    tenant = service.create_tenant(superadmin, tenant_payload)

    service.create_user(
        superadmin,
        tenant.id,
        UserInput(email="user1@client2.test", password="Secret123", roles=[TENANT_USER_ROLE]),
    )

    with pytest.raises(BusinessRuleViolation, match="maximum number of active users"):
        service.create_user(
            superadmin,
            tenant.id,
            UserInput(email="user2@client2.test", password="Secret123", roles=[TENANT_USER_ROLE]),
        )


def test_update_user_prevents_disabling_last_admin(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    plan = service.create_commercial_plan(superadmin, PlanCreateInput(name="Growth", max_users=5))
    tenant_payload = TenantCreateInput(
        name="Client Three",
        slug="client-three",
        companies=[_company()],
        administrators=[
            UserInput(email="admin@client3.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
        ],
        plan_id=plan.id,
    )
    tenant = service.create_tenant(superadmin, tenant_payload)

    admin_user = service.list_users(superadmin, tenant.id, include_inactive=True)[0]

    with pytest.raises(BusinessRuleViolation, match="at least one active tenant administrator"):
        service.update_user(superadmin, admin_user.id, UserUpdateInput(is_active=False))

    with pytest.raises(BusinessRuleViolation, match="at least one active tenant administrator"):
        service.update_user(superadmin, admin_user.id, UserUpdateInput(roles=[TENANT_USER_ROLE]))


def test_assign_plan_switches_active_subscription(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    starter = service.create_commercial_plan(superadmin, PlanCreateInput(name="Plan A", max_users=10))
    premium = service.create_commercial_plan(superadmin, PlanCreateInput(name="Plan B", max_users=25))

    tenant = service.create_tenant(
        superadmin,
        TenantCreateInput(
            name="Client Four",
            slug="client-four",
            companies=[_company()],
            administrators=[
                UserInput(email="admin@client4.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
            ],
            plan_id=starter.id,
        ),
    )

    service.assign_plan_to_tenant(superadmin, tenant.id, premium.id)

    subscriptions = service.session.execute(
        select(TenantPlanSubscription).where(TenantPlanSubscription.tenant_id == tenant.id)
    ).scalars().all()
    active = [subscription for subscription in subscriptions if subscription.is_active]

    assert len(active) == 1
    assert active[0].plan_id == premium.id
    assert any(not subscription.is_active for subscription in subscriptions)


def test_attach_companies_to_tenant(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    tenant = service.create_tenant(
        superadmin,
        TenantCreateInput(
            name="Client Five",
            slug="client-five",
            companies=[_company()],
            administrators=[
                UserInput(email="owner@client5.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
            ],
        ),
    )

    extra_companies = [
        CompanyInput(
            legal_name="Branch A",
            tax_id=uuid.uuid4().hex[:14],
            billing_email="branch-a@client5.test",
            address_line1="Street 1",
            city="Rio",
            state="RJ",
            zip_code="20000-000",
            country="BR",
        ),
        CompanyInput(
            legal_name="Branch B",
            tax_id=uuid.uuid4().hex[:14],
            billing_email="branch-b@client5.test",
            address_line1="Street 2",
            city="Rio",
            state="RJ",
            zip_code="20000-001",
            country="BR",
        ),
    ]

    created = service.attach_companies_to_tenant(superadmin, tenant.id, extra_companies)

    assert len(created) == 2
    stored = service.session.execute(
        select(TenantCompany).where(TenantCompany.tenant_id == tenant.id)
    ).scalars().all()
    assert len(stored) == 3


def test_suspend_and_reinstate_user(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    plan = service.create_commercial_plan(superadmin, PlanCreateInput(name="Ops", max_users=5))
    tenant = service.create_tenant(
        superadmin,
        TenantCreateInput(
            name="Client Six",
            slug="client-six",
            companies=[_company()],
            administrators=[
                UserInput(email="admin@client6.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
            ],
            plan_id=plan.id,
        ),
    )

    user = service.create_user(
        superadmin,
        tenant.id,
        UserInput(email="user@client6.test", password="Secret123", roles=[TENANT_USER_ROLE]),
    )

    suspended = service.suspend_user(superadmin, user.id, reason="Fraud investigation")
    assert suspended.is_suspended is True
    assert suspended.is_active is False
    assert suspended.suspension_reason == "Fraud investigation"

    reinstated = service.reinstate_user(superadmin, user.id, reactivate=True)
    assert reinstated.is_suspended is False
    assert reinstated.is_active is True
    assert reinstated.suspension_reason is None


def test_list_users_excludes_inactive_and_suspended(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    plan = service.create_commercial_plan(superadmin, PlanCreateInput(name="Scale", max_users=10))
    tenant = service.create_tenant(
        superadmin,
        TenantCreateInput(
            name="Client Seven",
            slug="client-seven",
            companies=[_company()],
            administrators=[
                UserInput(email="admin@client7.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
            ],
            plan_id=plan.id,
        ),
    )

    active = service.create_user(
        superadmin,
        tenant.id,
        UserInput(email="active@client7.test", password="Secret123", roles=[TENANT_USER_ROLE]),
    )
    inactive = service.create_user(
        superadmin,
        tenant.id,
        UserInput(email="inactive@client7.test", password="Secret123", roles=[TENANT_USER_ROLE]),
    )
    suspended = service.create_user(
        superadmin,
        tenant.id,
        UserInput(email="suspended@client7.test", password="Secret123", roles=[TENANT_USER_ROLE]),
    )

    # deactivate and suspend accordingly
    service.session.execute(
        select(User).where(User.id == inactive.id)
    ).scalar_one().is_active = False
    service.session.execute(
        select(User).where(User.id == suspended.id)
    ).scalar_one().is_suspended = True
    service.session.commit()

    users = service.list_users(superadmin, tenant.id)
    emails = {user.email for user in users}
    assert active.email in emails
    assert inactive.email not in emails
    assert suspended.email not in emails


def test_password_reset_flow(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    plan = service.create_commercial_plan(superadmin, PlanCreateInput(name="Support", max_users=5))
    tenant = service.create_tenant(
        superadmin,
        TenantCreateInput(
            name="Client Eight",
            slug="client-eight",
            companies=[_company()],
            administrators=[
                UserInput(email="admin@client8.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
            ],
            plan_id=plan.id,
        ),
    )

    user = service.create_user(
        superadmin,
        tenant.id,
        UserInput(email="user@client8.test", password="Secret123", roles=[TENANT_USER_ROLE]),
    )
    original_hash = service.session.execute(select(User).where(User.id == user.id)).scalar_one().hashed_password

    token = service.initiate_password_reset(superadmin, user.id)
    stored = service.session.execute(select(User).where(User.id == user.id)).scalar_one()
    assert stored.password_reset_token_hash is not None
    assert stored.password_reset_token_expires_at is not None

    updated = service.complete_password_reset(superadmin, user.id, token.token, "NewSecret123")
    refreshed = service.session.execute(select(User).where(User.id == updated.id)).scalar_one()
    assert refreshed.password_reset_token_hash is None
    assert verify_password("NewSecret123", refreshed.hashed_password)
    assert refreshed.hashed_password != original_hash


def test_update_commercial_plan_toggles_active(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    plan = service.create_commercial_plan(superadmin, PlanCreateInput(name="Enterprise"))
    updated = service.update_commercial_plan(
        superadmin,
        plan.id,
        PlanUpdateInput(is_active=False, max_users=50),
    )
    assert updated.is_active is False
    assert updated.max_users == 50


def test_list_tenants_scopes_for_admin(service: AdministrationService, default_tenant: Tenant, superadmin: ActingUser) -> None:
    tenant = service.create_tenant(
        superadmin,
        TenantCreateInput(
            name="Client Nine",
            slug="client-nine",
            companies=[_company()],
            administrators=[
                UserInput(email="admin@client9.test", password="Secret123", roles=[TENANT_ADMIN_ROLE])
            ],
        ),
    )
    admin_user = service.session.execute(select(User).where(User.email == "admin@client9.test")).scalar_one()
    tenant_admin = ActingUser(id=admin_user.id, tenant_id=tenant.id, roles=frozenset({TENANT_ADMIN_ROLE, TENANT_USER_ROLE}))

    tenants_for_admin = service.list_tenants(tenant_admin)
    assert {t.slug for t in tenants_for_admin} == {tenant.slug}

    tenants_for_super = service.list_tenants(superadmin)
    assert {t.slug for t in tenants_for_super} >= {tenant.slug, default_tenant.slug}
