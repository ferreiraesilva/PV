import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.models import (
    CommercialPlan,
    Tenant,
    TenantCompany,
    TenantPlanSubscription,
    User,
)
from app.db.session import get_db
from app.main import create_app


def test_administration_flow_e2e():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Tenant.__table__,
        TenantCompany.__table__,
        CommercialPlan.__table__,
        TenantPlanSubscription.__table__,
        User.__table__,
    ]
    app = None
    try:
        Base.metadata.create_all(engine, tables=tables)
        TestingSession = sessionmaker(
            bind=engine, autoflush=False, autocommit=False, future=True
        )

        app = create_app()

        def override_get_db():
            session: Session = TestingSession()
            try:
                yield session
                session.commit()
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db

        # seed default tenant required by administration service
        with TestingSession() as session:
            default_tenant = Tenant(
                name="Default", slug="default", is_active=True, is_default=True
            )
            session.add(default_tenant)
            session.commit()
            session.refresh(default_tenant)
            default_id = str(default_tenant.id)

        token = create_access_token(
            subject=str(uuid.uuid4()),
            extra_claims={"tenant_id": default_id, "roles": ["superadm"]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        with TestClient(app) as client:
            plan_response = client.post(
                "/v1/admin-portal/superuser/plans",
                headers=headers,
                json={
                    "name": "Premium",
                    "description": "Plano premium",
                    "maxUsers": 50,
                    "billingCycleMonths": 1,
                },
            )
            assert plan_response.status_code == 201
            plan_id = plan_response.json()["id"]

            tenant_response = client.post(
                "/v1/admin-portal/superuser/tenants",
                headers=headers,
                json={
                    "name": "Cliente E2E",
                    "slug": "cliente-e2e",
                    "planId": plan_id,
                    "companies": [
                        {
                            "legalName": "Cliente E2E LTDA",
                            "taxId": "12345678900000",
                            "billingEmail": "financeiro@clientee2e.com",
                            "addressLine1": "Rua Alpha 100",
                            "city": "Sao Paulo",
                            "state": "SP",
                            "zipCode": "01000-000",
                            "country": "BR",
                        }
                    ],
                    "administrators": [
                        {
                            "email": "admin@clientee2e.com",
                            "password": "Senha123",
                            "fullName": "Admin Cliente",
                            "roles": ["tenantadmin"],
                        }
                    ],
                },
            )
            assert tenant_response.status_code == 201
            tenant_id = tenant_response.json()["id"]

            # attach an additional company
            companies_response = client.post(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/companies",
                headers=headers,
                json={
                    "companies": [
                        {
                            "legalName": "Filial 1",
                            "taxId": "98765432100000",
                            "billingEmail": "financeiro@filial1.com",
                            "addressLine1": "Rua Beta 200",
                            "city": "Sao Paulo",
                            "state": "SP",
                            "zipCode": "02000-000",
                            "country": "BR",
                        }
                    ]
                },
            )
            assert companies_response.status_code == 201
            assert len(companies_response.json()) == 1

            # create additional tenant user
            user_response = client.post(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/users",
                headers=headers,
                json={
                    "email": "analyst@clientee2e.com",
                    "password": "Senha123",
                    "fullName": "Analista",
                    "roles": [],
                },
            )
            assert user_response.status_code == 201
            user_id = user_response.json()["id"]

            # suspend the user
            suspend_response = client.post(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/users/{user_id}/suspend",
                headers=headers,
                json={"reason": "Auditoria"},
            )
            assert suspend_response.status_code == 200
            assert suspend_response.json()["isSuspended"] is True

            # reinstate and reactivate the user
            reinstate_response = client.post(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/users/{user_id}/reinstate",
                headers=headers,
                json={"reactivate": True},
            )
            assert reinstate_response.status_code == 200
            assert reinstate_response.json()["isSuspended"] is False
            assert reinstate_response.json()["isActive"] is True

            # password reset flow
            reset_token_response = client.post(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/users/{user_id}/reset-password",
                headers=headers,
            )
            assert reset_token_response.status_code == 200
            token_payload = reset_token_response.json()
            assert token_payload["token"]

            confirm_response = client.post(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/users/{user_id}/reset-password/confirm",
                headers=headers,
                json={"token": token_payload["token"], "newPassword": "NovaSenha123"},
            )
            assert confirm_response.status_code == 200
            assert confirm_response.json()["email"] == "analyst@clientee2e.com"

            # verify users listing reflects updates
            users_listing = client.get(
                f"/v1/admin-portal/tenant-admin/{tenant_id}/users",
                headers=headers,
            )
            assert users_listing.status_code == 200
            users = users_listing.json()
            assert any(user["email"] == "analyst@clientee2e.com" for user in users)
    finally:
        Base.metadata.drop_all(engine, tables=tables)
        engine.dispose()
        if app is not None:
            app.dependency_overrides.pop(get_db, None)
