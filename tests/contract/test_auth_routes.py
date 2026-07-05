from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.api_gateway.app.api.deps import get_session
from services.api_gateway.app.auth.routes import router
from services.api_gateway.app.auth.service import (
    AuthInfrastructureError,
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from services.api_gateway.app.models import User

pytestmark = [pytest.mark.unit, pytest.mark.contract]


@pytest.fixture
def session_stub() -> object:
    return object()


@pytest.fixture
def client(session_stub: object) -> Iterator[TestClient]:
    app = FastAPI()

    async def fake_get_session() -> AsyncIterator[object]:
        yield session_stub

    app.dependency_overrides[get_session] = fake_get_session
    app.include_router(router)

    with TestClient(app) as test_client:
        yield test_client


def _make_user() -> User:
    return User(
        id=123,
        email="user@example.com",
        username=None,
        password_hash="hashed_password",
        created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )


def test_register_success_returns_201(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    async def fake_register(
        self: AuthService,
        *,
        email: str,
        password: str,
        username: str | None = None,
    ) -> User:
        assert self._session is session_stub
        assert email == "user@example.com"
        assert password == "password123"
        assert username is None

        return _make_user()

    monkeypatch.setattr(AuthService, "register", fake_register)

    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 123,
        "email": "user@example.com",
        "username": None,
        "created_at": "2026-01-02T03:04:05Z",
    }


def test_register_duplicate_email_returns_409(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_register(
        self: AuthService,
        *,
        email: str,
        password: str,
        username: str | None = None,
    ) -> User:
        raise EmailAlreadyRegisteredError("duplicate")

    monkeypatch.setattr(AuthService, "register", fake_register)

    response = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_infrastructure_error_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_register(
        self: AuthService,
        *,
        email: str,
        password: str,
        username: str | None = None,
    ) -> User:
        raise AuthInfrastructureError("db down")

    monkeypatch.setattr(AuthService, "register", fake_register)

    response = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}


def test_register_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/auth/register", json={"email": "not-an-email", "password": "short"})

    assert response.status_code == 422


def test_login_success_returns_200(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    session_stub: object,
) -> None:
    async def fake_login(
        self: AuthService,
        *,
        email: str,
        password: str,
    ) -> str:
        assert self._session is session_stub
        assert email == "user@example.com"
        assert password == "password123"

        return "success token"

    monkeypatch.setattr(AuthService, "login", fake_login)

    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 200
    assert response.json() == {"access_token": "success token", "token_type": "bearer"}


def test_login_invalid_credentials_returns_401(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_login(
        self: AuthService,
        *,
        email: str,
        password: str,
    ) -> str:
        raise InvalidCredentialsError("invalid")

    monkeypatch.setattr(AuthService, "login", fake_login)

    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_infrastructure_error_returns_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_login(
        self: AuthService,
        *,
        email: str,
        password: str,
    ) -> str:
        raise AuthInfrastructureError("db down")

    monkeypatch.setattr(AuthService, "login", fake_login)

    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password123"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}


def test_login_invalid_payload_returns_422(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = client.post("/auth/login", json={"email": "not-an-email", "password": "short"})

    assert response.status_code == 422
