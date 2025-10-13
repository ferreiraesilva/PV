from uuid import UUID
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.api.routes.admin_portal import get_administration_service
from app.core.roles import SUPERADMIN_ROLE
from tests.conftest import TENANT_ID, app


@pytest.fixture()
def _clear_overrides():
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_administration_service, None)


def test_create_plan_requires_superadmin(client, auth_headers, _clear_overrides):
    response = client.post(
        "/v1/admin-portal/superuser/plans",
        headers=auth_headers,
        json={
            "name": "Enterprise",
            "billingCycleMonths": 12,
        },
    )
    assert response.status_code == 403


def test_create_plan_returns_payload(client, superadmin_headers, _clear_overrides):
    captured = {}

    class StubService:
        def create_commercial_plan(self, acting_user, payload):
            captured["acting_user"] = acting_user
            captured["payload"] = payload
            return SimpleNamespace(
                id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                name=payload.name,
                description=payload.description,
                max_users=payload.max_users,
                price_cents=payload.price_cents,
                currency=payload.currency,
                is_active=True,
                billing_cycle_months=payload.billing_cycle_months,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.post(
        "/v1/admin-portal/superuser/plans",
        headers=superadmin_headers,
        json={
            "name": "Enterprise",
            "description": "Full feature plan",
            "maxUsers": 50,
            "priceCents": 19900,
            "currency": "BRL",
            "billingCycleMonths": 1,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Enterprise"
    assert captured["acting_user"].roles == frozenset({SUPERADMIN_ROLE})
    assert captured["payload"].name == "Enterprise"
    assert captured["payload"].max_users == 50


def test_list_plans_passes_include_flag(client, superadmin_headers, _clear_overrides):
    captured = {}

    class StubService:
        def list_commercial_plans(self, acting_user, include_inactive=False):
            captured["acting_user"] = acting_user
            captured["include_inactive"] = include_inactive
            return [
                SimpleNamespace(
                    id=uuid.uuid4(),
                    tenant_id=uuid.uuid4(),
                    name="Standard",
                    description=None,
                    max_users=None,
                    price_cents=None,
                    currency="BRL",
                    is_active=True,
                    billing_cycle_months=12,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            ]

    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.get(
        "/v1/admin-portal/superuser/plans?include_inactive=true",
        headers=superadmin_headers,
    )

    assert response.status_code == 200
    assert captured["include_inactive"] is True
    assert captured["acting_user"].roles == frozenset({SUPERADMIN_ROLE})
    assert response.json()[0]["name"] == "Standard"


def test_update_plan_forwards_payload(client, superadmin_headers, _clear_overrides):
    captured = {}

    class StubService:
        def update_commercial_plan(self, acting_user, plan_id, payload):
            captured["acting_user"] = acting_user
            captured["plan_id"] = plan_id
            captured["payload"] = payload
            return SimpleNamespace(
                id=plan_id,
                tenant_id=uuid.uuid4(),
                name=payload.name or "Standard",
                description=payload.description,
                max_users=payload.max_users,
                price_cents=payload.price_cents,
                currency=payload.currency or "BRL",
                is_active=payload.is_active,
                billing_cycle_months=payload.billing_cycle_months or 12,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    plan_id = uuid.uuid4()
    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.patch(
        f"/v1/admin-portal/superuser/plans/{plan_id}",
        headers=superadmin_headers,
        json={"isActive": False, "maxUsers": 99},
    )

    assert response.status_code == 200
    assert captured["plan_id"] == plan_id
    assert captured["payload"].is_active is False
    assert captured["payload"].max_users == 99


def test_attach_companies_maps_payload(client, superadmin_headers, _clear_overrides):
    captured = {}

    class StubService:
        def attach_companies_to_tenant(self, acting_user, tenant_id, companies):
            captured["acting_user"] = acting_user
            captured["tenant_id"] = tenant_id
            captured["companies"] = companies
            return [
                SimpleNamespace(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    legal_name=company.legal_name,
                    trade_name=company.trade_name,
                    tax_id=company.tax_id,
                    billing_email=company.billing_email,
                    billing_phone=company.billing_phone,
                    address_line1=company.address_line1,
                    address_line2=company.address_line2,
                    city=company.city,
                    state=company.state,
                    zip_code=company.zip_code,
                    country=company.country,
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                for company in companies
            ]

    tenant_id = uuid.uuid4()
    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.post(
        f"/v1/admin-portal/tenant-admin/{tenant_id}/companies",
        headers=superadmin_headers,
        json={
            "companies": [
                {
                    "legalName": "ACME",
                    "taxId": "123",
                    "billingEmail": "finance@acme.com",
                    "addressLine1": "Street",
                    "city": "Sao Paulo",
                    "state": "SP",
                    "zipCode": "01000-000",
                    "country": "BR",
                }
            ]
        },
    )

    assert response.status_code == 201
    assert captured["tenant_id"] == tenant_id
    assert captured["companies"][0].legal_name == "ACME"
    body = response.json()
    assert body[0]["legalName"] == "ACME"


def test_create_user_forwards_payload(client, superadmin_headers, _clear_overrides):
    captured = {}

    class StubService:
        def create_user(self, acting_user, tenant_id, payload):
            captured["acting_user"] = acting_user
            captured["tenant_id"] = tenant_id
            captured["payload"] = payload
            return SimpleNamespace(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                email=payload.email,
                full_name=payload.full_name,
                roles=list(payload.roles or []),
                is_active=True,
                is_superuser=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.post(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/users",
        headers=superadmin_headers,
        json={
            "email": "user@example.com",
            "password": "Str0ngPass!",
            "fullName": "Example User",
            "roles": ["tenantadmin"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert captured["tenant_id"].hex == TENANT_ID.replace("-", "")
    assert captured["payload"].email == "user@example.com"
    assert "tenantadmin" in captured["payload"].roles


def test_suspend_user_invokes_service(client, superadmin_headers, _clear_overrides):
    captured = {}

    tenant_uuid = uuid.UUID(TENANT_ID)

    class StubService:
        def get_user(self, acting_user, user_id):
            captured.setdefault("calls", []).append("get_user")
            return SimpleNamespace(id=user_id, tenant_id=tenant_uuid)

        def suspend_user(self, acting_user, user_id, reason=None):
            captured.setdefault("calls", []).append("suspend_user")
            captured["acting_user"] = acting_user
            captured["user_id"] = user_id
            captured["reason"] = reason
            return SimpleNamespace(
                id=user_id,
                tenant_id=tenant_uuid,
                email="suspended@example.com",
                full_name="Suspended",
                roles=["user"],
                is_active=False,
                is_superuser=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_administration_service] = lambda: StubService()
    user_id = uuid.uuid4()

    response = client.post(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/users/{user_id}/suspend",
        headers=superadmin_headers,
        json={"reason": "fraud"},
    )

    assert response.status_code == 200
    assert "suspend_user" in captured.get("calls", [])
    assert captured["user_id"] == user_id
    assert captured["reason"] == "fraud"


def test_initiate_password_reset_returns_token(
    client, superadmin_headers, _clear_overrides
):
    tenant_uuid = uuid.UUID(TENANT_ID)

    class StubToken:
        def __init__(self, token):
            self.token = token
            self.expires_at = datetime.now(timezone.utc)

    class StubService:
        def get_user(self, acting_user, user_id):
            return SimpleNamespace(id=user_id, tenant_id=tenant_uuid)

        def initiate_password_reset(self, acting_user, user_id):
            return StubToken("token123")

    app.dependency_overrides[get_administration_service] = lambda: StubService()
    user_id = uuid.uuid4()

    response = client.post(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/users/{user_id}/reset-password",
        headers=superadmin_headers,
    )

    assert response.status_code == 200
    assert response.json()["token"] == "token123"


def test_confirm_password_reset_calls_service(
    client, superadmin_headers, _clear_overrides
):
    tenant_uuid = uuid.UUID(TENANT_ID)
    captured = {}

    class StubService:
        def get_user(self, acting_user, user_id):
            return SimpleNamespace(id=user_id, tenant_id=tenant_uuid)

        def complete_password_reset(self, acting_user, user_id, token, new_password):
            captured["acting_user"] = acting_user
            captured["user_id"] = user_id
            captured["token"] = token
            captured["password"] = new_password
            return SimpleNamespace(
                id=user_id,
                tenant_id=tenant_uuid,
                email="user@example.com",
                full_name="Example",
                roles=["user"],
                is_active=True,
                is_superuser=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_administration_service] = lambda: StubService()
    user_id = uuid.uuid4()

    response = client.post(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/users/{user_id}/reset-password/confirm",
        headers=superadmin_headers,
        json={"token": "abc", "newPassword": "Secret123"},
    )

    assert response.status_code == 200
    assert captured["token"] == "abc"
    assert captured["password"] == "Secret123"


def test_create_payment_plan_template_requires_admin(
    client, auth_headers, _clear_overrides
):
    response = client.post(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/payment-plans",
        headers=auth_headers,
        json={
            "productCode": "vip",
            "principal": 5000,
            "discountRate": 0.02,
            "installments": [{"period": 1, "amount": 2500}],
        },
    )
    assert response.status_code == 403


def test_create_payment_plan_template_returns_payload(
    client, superadmin_headers, _clear_overrides
):
    captured = {}

    class StubService:
        def create_payment_plan_template(self, acting_user, tenant_id, payload):
            captured["acting_user"] = acting_user
            captured["tenant_id"] = tenant_id
            captured["payload"] = payload
            now = datetime.now(timezone.utc)
            return SimpleNamespace(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                product_code=payload.product_code,
                name=payload.name,
                description=payload.description,
                principal=payload.principal,
                discount_rate=payload.discount_rate,
                metadata_json=payload.metadata,
                is_active=payload.is_active,
                created_at=now,
                updated_at=now,
                installments=[
                    SimpleNamespace(
                        id=uuid.uuid4(), period=item.period, amount=item.amount
                    )
                    for item in payload.installments
                ],
            )

    app.dependency_overrides[get_administration_service] = lambda: StubService()

    payload = {
        "productCode": "vip",
        "label": "Plano VIP",
        "principal": 6000,
        "discountRate": 0.025,
        "installments": [
            {"period": 1, "amount": 3000},
            {"period": 2, "amount": 3200},
        ],
    }
    response = client.post(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/payment-plans",
        headers=superadmin_headers,
        json=payload,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["productCode"] == "vip"
    assert len(body["installments"]) == 2
    assert captured["tenant_id"] == UUID(TENANT_ID)


def test_list_payment_plan_templates_returns_collection(
    client, superadmin_headers, _clear_overrides
):
    expected = [
        SimpleNamespace(
            id=uuid.uuid4(),
            tenant_id=UUID(TENANT_ID),
            product_code="standard",
            name="Plano Standard",
            description=None,
            principal=4000,
            discount_rate=0.015,
            metadata_json=None,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            installments=[
                SimpleNamespace(id=uuid.uuid4(), period=1, amount=2000),
                SimpleNamespace(id=uuid.uuid4(), period=2, amount=2100),
            ],
        )
    ]

    class StubService:
        def list_payment_plan_templates(
            self, acting_user, tenant_id, include_inactive: bool = False
        ):
            return expected

    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.get(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/payment-plans",
        headers=superadmin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["productCode"] == "standard"


def test_update_payment_plan_template_calls_service(
    client, superadmin_headers, _clear_overrides
):
    captured = {}
    template_id = uuid.uuid4()

    class StubService:
        def update_payment_plan_template(
            self, acting_user, tenant_id, update_id, payload
        ):
            captured["tenant_id"] = tenant_id
            captured["update_id"] = update_id
            captured["payload"] = payload
            now = datetime.now(timezone.utc)
            return SimpleNamespace(
                id=update_id,
                tenant_id=tenant_id,
                product_code="standard",
                name=payload.name,
                description=payload.description,
                principal=payload.principal or 5000,
                discount_rate=payload.discount_rate or 0.02,
                metadata_json=payload.metadata,
                is_active=payload.is_active if payload.is_active is not None else True,
                created_at=now,
                updated_at=now,
                installments=[
                    SimpleNamespace(
                        id=uuid.uuid4(), period=item.period, amount=item.amount
                    )
                    for item in (payload.installments or [])
                ]
                or [SimpleNamespace(id=uuid.uuid4(), period=1, amount=2500)],
            )

    app.dependency_overrides[get_administration_service] = lambda: StubService()

    response = client.patch(
        f"/v1/admin-portal/tenant-admin/{TENANT_ID}/payment-plans/{template_id}",
        headers=superadmin_headers,
        json={
            "name": "Plano Renovado",
            "principal": 7000,
            "installments": [
                {"period": 1, "amount": 3500},
                {"period": 2, "amount": 3600},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Plano Renovado"
    assert captured["tenant_id"] == UUID(TENANT_ID)
    assert captured["update_id"] == template_id
    assert len(body["installments"]) == 2
