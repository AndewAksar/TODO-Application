from __future__ import annotations

import importlib
from datetime import UTC, datetime
from typing import Any, cast

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.exc import SQLAlchemyError

pytestmark = [pytest.mark.unit, pytest.mark.contract]


@pytest.fixture
def runtime_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
    monkeypatch.setenv("JWT_SECRET_KEY", "bootstrap-secret")


@pytest.fixture
def auth_modules(runtime_env: None) -> dict[str, Any]:
    deps_module = importlib.import_module("services.api_gateway.app.api.deps")
    auth_module = importlib.import_module("services.api_gateway.app.auth.dependencies")
    models_module = importlib.import_module("services.api_gateway.app.models")
    repo_module = importlib.import_module("services.api_gateway.app.repositories.users")
    settings_module = importlib.import_module("services.api_gateway.app.settings")

    return {
        "get_session": deps_module.get_session,
        "get_current_user": auth_module.get_current_user,
        "user_model": models_module.User,
        "user_repository": repo_module.UserRepository,
        "settings": settings_module.settings,
    }


@pytest.fixture(autouse=True)
def jwt_test_settings(monkeypatch: pytest.MonkeyPatch, auth_modules: dict[str, Any]) -> None:
    settings_obj = auth_modules["settings"]
    monkeypatch.setattr(settings_obj, "JWT_SECRET_KEY", "test-secret-key", raising=True)
    monkeypatch.setattr(settings_obj, "JWT_ALGORITHM", "HS256", raising=True)
    monkeypatch.setattr(settings_obj, "JWT_EXPIRES_MINUTES", 15, raising=True)


@pytest.fixture
def client(auth_modules: dict[str, Any]) -> TestClient:
    app = FastAPI()

    async def fake_get_session():
        yield object()

    app.dependency_overrides[auth_modules["get_session"]] = fake_get_session

    @app.get("/test-protected")
    async def test_protected(
        current_user=Depends(auth_modules["get_current_user"]),
    ) -> dict[str, int]:
        return {"user_id": current_user.id}

    return TestClient(app)


def _make_token(payload: dict[str, object], auth_modules: dict[str, Any]) -> str:
    settings_obj = auth_modules["settings"]

    return cast(
        str,
        jwt.encode(
            payload,
            settings_obj.JWT_SECRET_KEY,
            algorithm=settings_obj.JWT_ALGORITHM,
        ),
    )


def test_get_current_user_returns_401_without_token(client: TestClient) -> None:
    response = client.get("/test-protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_get_current_user_returns_401_for_non_bearer_scheme(client: TestClient) -> None:
    response = client.get("/test-protected", headers={"Authorization": "Token abc"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_get_current_user_returns_401_for_garbage_token(client: TestClient) -> None:
    response = client.get(
        "/test-protected",
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_get_current_user_returns_401_for_expired_token(
    client: TestClient,
    auth_modules: dict[str, Any],
) -> None:
    expired_token = _make_token({"sub": "42", "iat": 1, "exp": 2}, auth_modules)

    response = client.get(
        "/test-protected",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_get_current_user_returns_401_when_user_not_found(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    auth_modules: dict[str, Any],
) -> None:
    async def fake_get_by_id(self: Any, user_id: int) -> None:
        return None

    monkeypatch.setattr(auth_modules["user_repository"], "get_by_id", fake_get_by_id)

    token = _make_token({"sub": "7", "iat": 1, "exp": 4_102_444_800}, auth_modules)

    response = client.get("/test-protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_get_current_user_returns_200_with_existing_user(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    auth_modules: dict[str, Any],
) -> None:
    user = auth_modules["user_model"](
        id=99,
        email="user@example.com",
        username="user",
        password_hash="hashed",
        created_at=datetime.now(UTC),
    )

    async def fake_get_by_id(self: Any, user_id: int) -> Any:
        return user

    monkeypatch.setattr(auth_modules["user_repository"], "get_by_id", fake_get_by_id)

    token = _make_token({"sub": "99", "iat": 1, "exp": 4_102_444_800}, auth_modules)

    response = client.get("/test-protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": 99}


def test_get_current_user_accepts_lowercase_bearer_scheme(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    auth_modules: dict[str, Any],
) -> None:
    user = auth_modules["user_model"](
        id=101,
        email="lowercase@example.com",
        username="lowercase",
        password_hash="hashed",
        created_at=datetime.now(UTC),
    )

    async def fake_get_by_id(self: Any, user_id: int) -> Any:
        return user

    monkeypatch.setattr(auth_modules["user_repository"], "get_by_id", fake_get_by_id)

    token = _make_token({"sub": "101", "iat": 1, "exp": 4_102_444_800}, auth_modules)

    response = client.get("/test-protected", headers={"Authorization": f"bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": 101}


def test_get_current_user_returns_503_for_db_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    auth_modules: dict[str, Any],
) -> None:
    async def fake_get_by_id(self: Any, user_id: int) -> None:
        raise SQLAlchemyError("db unavailable")

    monkeypatch.setattr(auth_modules["user_repository"], "get_by_id", fake_get_by_id)

    token = _make_token({"sub": "7", "iat": 1, "exp": 4_102_444_800}, auth_modules)

    response = client.get("/test-protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporarily unavailable"}
