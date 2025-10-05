from __future__ import annotations

from datetime import date
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services.simulation import AdjustmentLogic


@pytest.fixture
def mock_index_repository() -> Mock:
    """Fixture to create a mock FinancialIndexRepository."""
    return Mock()


class TestAdjustmentLogic:
    def test_apply_uses_addon_rate_as_fallback_when_no_index_values(self, mock_index_repository: Mock):
        """
        Verifica se, na ausência de valores de índice no banco, a lógica de reajuste
        utiliza a `addon_rate` para calcular a correção.
        """
        # Arrange
        mock_index_repository.list_by_index_code.return_value = []
        tenant_id = uuid4()
        addon_rate = 0.12  # 12% a.a.
        periods = [(1, 1000.0), (12, 1000.0)]

        logic = AdjustmentLogic(
            base_date=date(2024, 1, 15),
            index_code="INCC-CUSTOM",
            periodicity="monthly",
            addon_rate=addon_rate,
            index_repository=mock_index_repository,
            tenant_id=tenant_id,
        )

        # Act
        adjusted_periods = logic.apply(periods)

        # Assert
        # Verifica se o repositório foi consultado
        mock_index_repository.list_by_index_code.assert_called_once_with(tenant_id, "INCC-CUSTOM")

        # Valida o cálculo para a primeira parcela (1 mês)
        expected_amount_1 = 1000.0 * ((1 + addon_rate) ** (1 / 12))
        assert adjusted_periods[0][0] == 1
        assert adjusted_periods[0][1] == pytest.approx(expected_amount_1)

        # Valida o cálculo para a segunda parcela (12 meses)
        expected_amount_12 = 1000.0 * ((1 + addon_rate) ** (12 / 12))  # 1000 * 1.12
        assert adjusted_periods[1][0] == 12
        assert adjusted_periods[1][1] == pytest.approx(expected_amount_12)

    def test_apply_monthly_with_index_values(self, mock_index_repository: Mock):
        """
        Valida o reajuste mensal usando valores de índice do repositório.
        """
        # Arrange
        # Mock de valores de índice para 3 meses
        index_values = [
            Mock(reference_date=date(2024, 2, 1), value=1.01),  # Fev/24
            Mock(reference_date=date(2024, 3, 1), value=1.02),  # Mar/24
            Mock(reference_date=date(2024, 4, 1), value=1.005), # Abr/24
        ]
        mock_index_repository.list_by_index_code.return_value = index_values
        base_date = date(2024, 1, 15)
        addon_rate = 0.12  # 12% a.a.

        logic = AdjustmentLogic(
            base_date=base_date,
            index_code="INCC-CUSTOM",
            periodicity="monthly",
            addon_rate=addon_rate,
            index_repository=mock_index_repository,
            tenant_id=uuid4(),
        )
        # Parcela com vencimento em 3 meses (Abril)
        periods = [(3, 1000.0)]

        # Act
        adjusted_periods = logic.apply(periods)

        # Assert
        # Fator de correção = 1.01 (Fev) * 1.02 (Mar) * 1.005 (Abr)
        index_correction = 1.01 * 1.02 * 1.005
        # Fator de acréscimo para 3 meses
        addon_correction = (1 + addon_rate) ** (3 / 12)
        expected_amount = 1000.0 * index_correction * addon_correction

        assert adjusted_periods[0][1] == pytest.approx(expected_amount)

    def test_apply_anniversary_with_index_values(self, mock_index_repository: Mock):
        """
        Valida o reajuste por aniversário, que deve aplicar a correção acumulada
        apenas nos aniversários do contrato.
        """
        # Arrange
        # Mock de valores de índice para 12 meses
        index_values = [
            Mock(reference_date=date(2024, m + 1, 1), value=(1.005 + m * 0.0001)) for m in range(12)
        ]
        mock_index_repository.list_by_index_code.return_value = index_values
        base_date = date(2023, 12, 15)
        addon_rate = 0.10  # 10% a.a.

        logic = AdjustmentLogic(
            base_date=base_date,
            index_code="IGPM-CUSTOM",
            periodicity="anniversary",
            addon_rate=addon_rate,
            index_repository=mock_index_repository,
            tenant_id=uuid4(),
        )
        # Parcela 1: antes do 1º aniversário (mês 11)
        # Parcela 2: após o 1º aniversário (mês 13)
        periods = [(11, 1000.0), (13, 1000.0)]

        # Act
        adjusted_periods = logic.apply(periods)

        # Assert
        # Parcela 1 não deve ser reajustada
        assert adjusted_periods[0][1] == pytest.approx(1000.0)

        # Parcela 2 deve ser reajustada com o acumulado dos 12 meses + addon_rate
        index_correction = 1.0
        for v in index_values:
            index_correction *= v.value
        expected_amount = 1000.0 * index_correction * (1 + addon_rate)
        assert adjusted_periods[1][1] == pytest.approx(expected_amount)