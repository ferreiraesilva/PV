from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services.administration import (
    ActingUser,
    AdministrationService,
    BusinessRuleViolation,
    NotFoundError,
    PermissionDeniedError,
    TenantCreateInput,
    UserInput,
)


@pytest.fixture
def mock_repository() -> Mock:
    """Fixture to create a mock AdministrationRepository."""
    return Mock()


@pytest.fixture
def service(mock_repository: Mock) -> AdministrationService:
    """Fixture to create an AdministrationService with a mocked repository."""
    return AdministrationService(db=mock_repository)


@pytest.fixture
def superuser() -> ActingUser:
    return ActingUser(id=uuid4(), tenant_id=uuid4(), roles=frozenset(["superuser"]))


@pytest.fixture
def tenant_admin() -> ActingUser:
    return ActingUser(id=uuid4(), tenant_id=uuid4(), roles=frozenset(["tenant_admin"]))


@pytest.fixture
def regular_user() -> ActingUser:
    return ActingUser(id=uuid4(), tenant_id=uuid4(), roles=frozenset(["user"]))


class TestAdministrationService:
    def test_create_tenant_allowed_for_superuser(
        self, service: AdministrationService, superuser: ActingUser
    ):
        # Arrange
        service._repository.find_tenant_by_slug.return_value = None
        service._repository.create_tenant.return_value = Mock()
        tenant_input = TenantCreateInput(
            name="New Tenant", slug="new-tenant", companies=[], administrators=[]
        )

        # Act
        service.create_tenant(superuser, tenant_input)

        # Assert
        service._repository.create_tenant.assert_called_once()

    def test_create_tenant_denied_for_tenant_admin(
        self, service: AdministrationService, tenant_admin: ActingUser
    ):
        # Arrange
        tenant_input = TenantCreateInput(
            name="New Tenant", slug="new-tenant", companies=[], administrators=[]
        )

        # Act & Assert
        with pytest.raises(
            PermissionDeniedError, match="Only superusers can create new tenants"
        ):
            service.create_tenant(tenant_admin, tenant_input)

    def test_create_tenant_fails_if_slug_exists(
        self, service: AdministrationService, superuser: ActingUser
    ):
        # Arrange
        service._repository.find_tenant_by_slug.return_value = (
            Mock()
        )  # Simulate slug already exists
        tenant_input = TenantCreateInput(
            name="New Tenant", slug="existing-slug", companies=[], administrators=[]
        )

        # Act & Assert
        with pytest.raises(
            BusinessRuleViolation, match="Tenant slug 'existing-slug' is already in use"
        ):
            service.create_tenant(superuser, tenant_input)

    def test_create_user_allowed_for_tenant_admin_in_own_tenant(
        self, service: AdministrationService, tenant_admin: ActingUser
    ):
        # Arrange
        service._repository.find_user_by_email.return_value = None
        service._repository.get_tenant.return_value = Mock(id=tenant_admin.tenant_id)
        user_input = UserInput(
            email="new.user@test.com", password="password", roles=["user"]
        )

        # Act
        service.create_user(tenant_admin, tenant_admin.tenant_id, user_input)

        # Assert
        service._repository.create_user.assert_called_once()

    def test_create_user_denied_for_tenant_admin_in_other_tenant(
        self, service: AdministrationService, tenant_admin: ActingUser
    ):
        # Arrange
        other_tenant_id = uuid4()
        user_input = UserInput(
            email="new.user@test.com", password="password", roles=["user"]
        )

        # Act & Assert
        with pytest.raises(
            PermissionDeniedError,
            match="Tenant administrators can only manage their own tenant",
        ):
            service.create_user(tenant_admin, other_tenant_id, user_input)

    def test_create_user_fails_if_email_exists(
        self, service: AdministrationService, superuser: ActingUser
    ):
        # Arrange
        tenant_id = uuid4()
        service._repository.find_user_by_email.return_value = (
            Mock()
        )  # Simulate email already exists
        service._repository.get_tenant.return_value = Mock(id=tenant_id)
        user_input = UserInput(
            email="existing.user@test.com", password="password", roles=["user"]
        )

        # Act & Assert
        with pytest.raises(
            BusinessRuleViolation,
            match="User with email 'existing.user@test.com' already exists",
        ):
            service.create_user(superuser, tenant_id, user_input)

    def test_get_user_denied_for_regular_user(
        self, service: AdministrationService, regular_user: ActingUser
    ):
        # Arrange
        target_user_id = uuid4()

        # Act & Assert
        with pytest.raises(PermissionDeniedError):
            service.get_user(regular_user, target_user_id)

    def test_suspend_user_fails_if_user_not_found(
        self, service: AdministrationService, superuser: ActingUser
    ):
        # Arrange
        non_existent_user_id = uuid4()
        service._repository.get_user.return_value = None

        # Act & Assert
        with pytest.raises(
            NotFoundError, match=f"User with ID '{non_existent_user_id}' not found"
        ):
            service.suspend_user(superuser, non_existent_user_id, "test reason")

    def test_suspend_user_denied_when_suspending_self(
        self, service: AdministrationService, tenant_admin: ActingUser
    ):
        # Act & Assert
        with pytest.raises(
            BusinessRuleViolation, match="Users cannot suspend their own account"
        ):
            service.suspend_user(tenant_admin, tenant_admin.id, "test reason")
