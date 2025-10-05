from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services.administration import ActingUser, PermissionDeniedError
from app.services.financial_index import FinancialIndexService


@pytest.fixture
def mock_repository() -> Mock:
    return Mock()


@pytest.fixture
def service(mock_repository: Mock) -> FinancialIndexService:
    # O serviço é instanciado com um repositório mockado
    return FinancialIndexService(db=mock_repository)


@pytest.fixture
def superuser() -> ActingUser:
    return ActingUser(id=uuid4(), tenant_id=uuid4(), roles=frozenset(["superuser"]))


@pytest.fixture
def tenant_admin() -> ActingUser:
    return ActingUser(id=uuid4(), tenant_id=uuid4(), roles=frozenset(["tenant_admin"]))


class TestFinancialIndexServicePermissions:
    # --- Testes para list_values ---
    def test_list_values_allowed_for_superuser(self, service: FinancialIndexService, superuser: ActingUser):
        # Superuser pode listar índices de qualquer tenant
        other_tenant_id = uuid4()
        service.list_values(superuser, other_tenant_id, "INCC")
        service._repository.list_by_index_code.assert_called_once_with(other_tenant_id, "INCC")

    def test_list_values_allowed_for_own_tenant_admin(self, service: FinancialIndexService, tenant_admin: ActingUser):
        # Tenant admin pode listar índices do seu próprio tenant
        service.list_values(tenant_admin, tenant_admin.tenant_id, "INCC")
        service._repository.list_by_index_code.assert_called_once_with(tenant_admin.tenant_id, "INCC")

    def test_list_values_denied_for_other_tenant(self, service: FinancialIndexService, tenant_admin: ActingUser):
        # Tenant admin NÃO pode listar índices de outro tenant
        other_tenant_id = uuid4()
        with pytest.raises(PermissionDeniedError):
            service.list_values(tenant_admin, other_tenant_id, "INCC")

    # --- Testes para create_or_update_values ---
    def test_create_values_allowed_for_superuser(self, service: FinancialIndexService, superuser: ActingUser):
        # Superuser pode criar/atualizar índices para qualquer tenant
        other_tenant_id = uuid4()
        service.create_or_update_values(superuser, other_tenant_id, "INCC", values=[Mock()])
        service._repository.create_or_update_values.assert_called_once()

    def test_create_values_allowed_for_own_tenant_admin(self, service: FinancialIndexService, tenant_admin: ActingUser):
        # Tenant admin pode criar/atualizar índices do seu próprio tenant
        service.create_or_update_values(tenant_admin, tenant_admin.tenant_id, "INCC", values=[Mock()])
        service._repository.create_or_update_values.assert_called_once()

    def test_create_values_denied_for_other_tenant(self, service: FinancialIndexService, tenant_admin: ActingUser):
        # Tenant admin NÃO pode criar/atualizar índices de outro tenant
        other_tenant_id = uuid4()
        with pytest.raises(PermissionDeniedError):
            service.create_or_update_values(tenant_admin, other_tenant_id, "INCC", values=[Mock()])

    def test_create_values_denied_for_regular_user(self, service: FinancialIndexService):
        # Usuário comum não pode criar/atualizar índices
        regular_user = ActingUser(id=uuid4(), tenant_id=uuid4(), roles=frozenset(["user"]))
        with pytest.raises(PermissionDeniedError):
            service.create_or_update_values(regular_user, regular_user.tenant_id, "INCC", values=[Mock()])

    def test_create_values_with_empty_list_does_not_call_repo(self, service: FinancialIndexService, tenant_admin: ActingUser):
        # Se a lista de valores for vazia, o repositório não deve ser chamado
        result = service.create_or_update_values(tenant_admin, tenant_admin.tenant_id, "INCC", values=[])
        assert result == []
        service._repository.create_or_update_values.assert_not_called()