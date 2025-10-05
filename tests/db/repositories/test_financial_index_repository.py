from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.api.schemas.financial_index import IndexValueInput
from app.db.models.financial_index import FinancialIndexValue
from app.db.repositories.financial_index import FinancialIndexRepository

# Mark all tests in this file as needing the 'db_session' fixture
pytestmark = pytest.mark.usefixtures("db_session")


class TestFinancialIndexRepository:
    def test_list_by_index_code_returns_correct_data(self, db_session: Session):
        # Arrange
        repo = FinancialIndexRepository(db_session)
        tenant_id1 = uuid4()
        tenant_id2 = uuid4()
        db_session.add_all([
            FinancialIndexValue(tenant_id=tenant_id1, index_code="INCC", reference_date=date(2024, 2, 1), value=1.02),
            FinancialIndexValue(tenant_id=tenant_id1, index_code="INCC", reference_date=date(2024, 1, 1), value=1.01),
            FinancialIndexValue(tenant_id=tenant_id1, index_code="IGPM", reference_date=date(2024, 1, 1), value=1.03),
            FinancialIndexValue(tenant_id=tenant_id2, index_code="INCC", reference_date=date(2024, 1, 1), value=1.04),
        ])
        db_session.commit()

        # Act
        results = repo.list_by_index_code(tenant_id1, "INCC")

        # Assert
        assert len(results) == 2
        assert results[0].reference_date == date(2024, 1, 1)
        assert results[0].value == 1.01
        assert results[1].reference_date == date(2024, 2, 1)
        assert results[1].value == 1.02

    def test_create_or_update_values_creates_new_records(self, db_session: Session):
        # Arrange
        repo = FinancialIndexRepository(db_session)
        tenant_id = uuid4()
        values_to_create = [
            IndexValueInput(reference_date=date(2024, 1, 1), value=1.05),
            IndexValueInput(reference_date=date(2024, 2, 1), value=1.06),
        ]

        # Act
        repo.create_or_update_values(tenant_id, "INCC-M", values_to_create)
        db_session.commit()

        # Assert
        results = db_session.query(FinancialIndexValue).filter_by(tenant_id=tenant_id).all()
        assert len(results) == 2
        assert results[0].value == 1.05

    def test_create_or_update_values_updates_existing_records(self, db_session: Session):
        # Arrange
        repo = FinancialIndexRepository(db_session)
        tenant_id = uuid4()
        existing_record = FinancialIndexValue(tenant_id=tenant_id, index_code="INCC-M", reference_date=date(2024, 1, 1), value=1.0)
        db_session.add(existing_record)
        db_session.commit()

        values_to_update = [IndexValueInput(reference_date=date(2024, 1, 1), value=1.5)]

        # Act
        repo.create_or_update_values(tenant_id, "INCC-M", values_to_update)
        db_session.commit()

        # Assert
        results = db_session.query(FinancialIndexValue).filter_by(tenant_id=tenant_id).all()
        assert len(results) == 1
        assert results[0].value == 1.5

    def test_create_or_update_values_handles_mixed_create_and_update(self, db_session: Session):
        # Arrange
        repo = FinancialIndexRepository(db_session)
        tenant_id = uuid4()
        existing_record = FinancialIndexValue(tenant_id=tenant_id, index_code="INCC-M", reference_date=date(2024, 1, 1), value=1.0)
        db_session.add(existing_record)
        db_session.commit()

        values = [
            IndexValueInput(reference_date=date(2024, 1, 1), value=1.99),  # Update
            IndexValueInput(reference_date=date(2024, 2, 1), value=2.0),   # Create
        ]

        # Act
        repo.create_or_update_values(tenant_id, "INCC-M", values)
        db_session.commit()

        # Assert
        results = db_session.query(FinancialIndexValue).order_by(FinancialIndexValue.reference_date).all()
        assert len(results) == 2
        assert results[0].value == 1.99
        assert results[1].value == 2.0