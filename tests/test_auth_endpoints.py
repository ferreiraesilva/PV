from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.models import User
from app.db.repositories.user import UserRepository
from app.db.repositories.refresh_token import RefreshTokenRepository

TENANT_ID = "11111111-1111-1111-1111-111111111111"
USER_ID = "44444444-4444-4444-4444-444444444444"


@pytest.fixture
def mock_user_repository(monkeypatch) -> MagicMock:
    mock = MagicMock(spec=UserRepository)
    monkeypatch.setattr("app.api.routes.auth.UserRepository", lambda _: mock)
    return mock


@pytest.fixture
def mock_refresh_token_repository(monkeypatch) -> MagicMock:
    mock = MagicMock(spec=RefreshTokenRepository)
    monkeypatch.setattr("app.api.routes.auth.RefreshTokenRepository", lambda _: mock)
    return mock


def test_login_unscoped_success(
    client: TestClient,
    mock_user_repository: MagicMock,
    mock_refresh_token_repository: MagicMock,
):
    # Arrange
    email = "test@example.com"
    password = "password"
    user = User(
        id=USER_ID,
        tenant_id=TENANT_ID,
        email=email,
        hashed_password="hashed:password",  # Using the stubbed password context from conftest
        is_active=True,
        is_suspended=False,
    )
    mock_user_repository.get_by_email_unscoped.return_value = [user]

    # Act
    response = client.post("/v1/login", json={"email": email, "password": password})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    mock_user_repository.get_by_email_unscoped.assert_called_once_with(email)
    mock_refresh_token_repository.create.assert_called_once()


def test_login_unscoped_invalid_credentials(
    client: TestClient, mock_user_repository: MagicMock
):
    # Arrange
    email = "test@example.com"
    password = "wrong_password"
    user = User(
        id=USER_ID,
        tenant_id=TENANT_ID,
        email=email,
        hashed_password="hashed:password",
        is_active=True,
        is_suspended=False,
    )
    mock_user_repository.get_by_email_unscoped.return_value = [user]

    # Act
    response = client.post("/v1/login", json={"email": email, "password": password})

    # Assert
    assert response.status_code == 401
    data = response.json()
    assert data["message"] == "Invalid credentials"


def test_login_unscoped_inactive_user(
    client: TestClient, mock_user_repository: MagicMock
):
    # Arrange
    email = "test@example.com"
    password = "password"
    user = User(
        id=USER_ID,
        tenant_id=TENANT_ID,
        email=email,
        hashed_password="hashed:password",
        is_active=False,
        is_suspended=False,
    )
    mock_user_repository.get_by_email_unscoped.return_value = [user]

    # Act
    response = client.post("/v1/login", json={"email": email, "password": password})

    # Assert
    assert response.status_code == 403
    data = response.json()
    assert data["message"] == "User account is inactive"


def test_login_unscoped_suspended_user(
    client: TestClient, mock_user_repository: MagicMock
):
    # Arrange
    email = "test@example.com"
    password = "password"
    user = User(
        id=USER_ID,
        tenant_id=TENANT_ID,
        email=email,
        hashed_password="hashed:password",
        is_active=True,
        is_suspended=True,
    )
    mock_user_repository.get_by_email_unscoped.return_value = [user]

    # Act
    response = client.post("/v1/login", json={"email": email, "password": password})

    # Assert
    assert response.status_code == 403
    data = response.json()
    assert data["message"] == "User account is suspended"


def test_login_scoped_success(
    client: TestClient,
    mock_user_repository: MagicMock,
    mock_refresh_token_repository: MagicMock,
):
    # Arrange
    email = "test@example.com"
    password = "password"
    user = User(
        id=USER_ID,
        tenant_id=TENANT_ID,
        email=email,
        hashed_password="hashed:password",
        is_active=True,
        is_suspended=False,
    )
    mock_user_repository.get_by_email.return_value = user

    # Act
    response = client.post(
        f"/v1/t/{TENANT_ID}/login", json={"email": email, "password": password}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    mock_user_repository.get_by_email.assert_called_once_with(TENANT_ID, email)
    mock_refresh_token_repository.create.assert_called_once()
