from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from services.api_gateway.app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from services.api_gateway.app.models import User

pytestmark = pytest.mark.unit


class UserORMStub:
    def __init__(
        self,
        user_id: int,
        email: str,
        username: str | None,
        created_at: datetime,
        password_hash: str,
        tasks: list[str],
    ) -> None:
        self.id = user_id
        self.email = email
        self.username = username
        self.created_at = created_at
        self.password_hash = password_hash
        self.tasks = tasks


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schemas_accept_valid_payload(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    payload = {
        "email": "test@example.com",
        "password": "password123",
    }

    schema = schema_cls(**payload)

    assert schema.email == payload["email"]
    assert schema.password == payload["password"]


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schema_rejects_invalid_email(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    with pytest.raises(ValidationError):
        schema_cls(email="invalid_email", password="password123")


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schema_rejects_empty_password(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    with pytest.raises(ValidationError):
        schema_cls(email="test@example.com", password="")


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schema_rejects_too_short_password(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    with pytest.raises(ValidationError):
        schema_cls.model_validate(
            {
                "email": "test@example.com",
                "password": "short",
            }
        )


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schema_rejects_too_long_password(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    with pytest.raises(ValidationError):
        schema_cls.model_validate(
            {
                "email": "test@example.com",
                "password": "a" * 129,
            }
        )


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schema_rejects_missing_password(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    with pytest.raises(ValidationError):
        schema_cls.model_validate({"email": "test@example.com"})


@pytest.mark.parametrize("schema_cls", [RegisterRequest, LoginRequest])
def test_auth_request_schema_rejects_unknown_fields(
    schema_cls: type[RegisterRequest | LoginRequest],
) -> None:
    with pytest.raises(ValidationError):
        schema_cls.model_validate(
            {
                "email": "test@example.com",
                "password": "password123",
                "unexpected": "value",
            }
        )


def test_token_response_defaults_to_bearer() -> None:
    response = TokenResponse(access_token="jwt-token")

    assert response.token_type == "bearer"
    assert response.model_dump() == {
        "access_token": "jwt-token",
        "token_type": "bearer",
    }


def test_token_response_rejects_non_bearer_token_type() -> None:
    with pytest.raises(ValidationError):
        TokenResponse.model_validate({"access_token": "jwt-token", "token_type": "not-bearer"})


def test_user_response_can_be_built_from_orm_attributes() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    user = UserORMStub(
        user_id=1,
        email="test@example.com",
        username="test_user",
        created_at=created_at,
        password_hash="hashed_password",
        tasks=["task-1"],
    )

    response = UserResponse.model_validate(user)

    assert response.model_dump() == {
        "id": 1,
        "email": "test@example.com",
        "username": "test_user",
        "created_at": created_at,
    }

    assert "password_hash" not in response.model_dump()


def test_user_response_rejects_invalid_email_from_attributes() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    user = UserORMStub(
        user_id=1,
        email="invalid_email",
        username=None,
        created_at=created_at,
        password_hash="hashed_password",
        tasks=[],
    )

    with pytest.raises(ValidationError):
        UserResponse.model_validate(user)


def test_user_response_from_sqlalchemy_model_hides_sensitive_fields() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    user = User(
        id=1,
        email="test@example.com",
        username="test_user",
        password_hash="hashed_password",
        created_at=created_at,
    )

    response = UserResponse.model_validate(user)

    assert response.id == 1
    assert response.email == "test@example.com"
    assert response.username == "test_user"
    assert "password_hash" not in response.model_dump()
