from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from services.api_gateway.app.auth.service import (
    AuthInfrastructureError,
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from services.api_gateway.app.models import User
from services.api_gateway.app.security.jwt import TokenError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

pytestmark = pytest.mark.unit


@pytest.fixture
def session_mock() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def service(session_mock: AsyncMock) -> AuthService:
    return AuthService(session_mock)


def _make_user(user_id: int = 1, email: str = "user@example.com") -> User:
    return User(
        id=user_id,
        email=email,
        username="user",
        password_hash="hash-password",
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_register_success_returns_user_and_commits(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_user = _make_user()

    get_by_email_mock = AsyncMock(return_value=None)
    create_user_mock = AsyncMock(return_value=created_user)
    hash_password_mock = Mock(return_value="hashed")

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(service._users, "create_user", create_user_mock)
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.hash_password",
        hash_password_mock,
    )

    result = await service.register(email="user@example.com", password="password123")

    assert result is created_user
    hash_password_mock.assert_called_once_with("password123")
    session_mock.commit.assert_awaited_once()
    session_mock.rollback.assert_not_awaited()

    create_user_mock.assert_awaited_once_with(
        email="user@example.com",
        password_hash="hashed",
        username=None,
    )


@pytest.mark.asyncio
async def test_register_duplicate_email_raises_and_does_not_create_user(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=_make_user())
    create_user_mock = AsyncMock()

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(service._users, "create_user", create_user_mock)

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(email="user@example.com", password="password123")

    create_user_mock.assert_not_called()
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_get_by_email_sqlalchemy_error_rolls_back_and_raises_infra(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(side_effect=SQLAlchemyError("db down"))
    create_user_mock = AsyncMock()

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(service._users, "create_user", create_user_mock)

    with pytest.raises(AuthInfrastructureError):
        await service.register(email="user@example.com", password="password123")

    create_user_mock.assert_not_called()
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_integrity_error_rolls_back_and_raises_duplicate(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=None)
    create_user_mock = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("dup")))

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(service._users, "create_user", create_user_mock)
    monkeypatch.setattr("services.api_gateway.app.auth.service.hash_password", lambda pwd: "hashed")

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(email="user@example.com", password="password123")

    create_user_mock.assert_awaited_once_with(
        email="user@example.com",
        password_hash="hashed",
        username=None,
    )
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_register_generic_sqlalchemy_error_rolls_back_and_raises_infra(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=None)
    create_user_mock = AsyncMock(side_effect=SQLAlchemyError("db down"))

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(service._users, "create_user", create_user_mock)
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.hash_password",
        lambda pwd: "hashed",
    )

    with pytest.raises(AuthInfrastructureError):
        await service.register(email="user@example.com", password="password123")

    create_user_mock.assert_awaited_once_with(
        email="user@example.com",
        password_hash="hashed",
        username=None,
    )
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_success_returns_token(
    service: AuthService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _make_user(user_id=123)
    get_by_email_mock = AsyncMock(return_value=user)
    verify_password_mock = Mock(return_value=True)
    create_access_token_mock = Mock(return_value="token")

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.verify_password",
        verify_password_mock,
    )
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.create_access_token",
        create_access_token_mock,
    )

    token = await service.login(email="user@example.com", password="password123")

    assert token == "token"
    get_by_email_mock.assert_awaited_once_with("user@example.com")
    verify_password_mock.assert_called_once_with("password123", "hash-password")
    create_access_token_mock.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_login_get_by_email_sqlalchemy_error_rolls_back_and_raises_infra(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(side_effect=SQLAlchemyError("db down"))

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)

    with pytest.raises(AuthInfrastructureError):
        await service.login(email="user@example.com", password="password123")

    get_by_email_mock.assert_awaited_once_with("user@example.com")
    session_mock.rollback.assert_awaited_once()
    session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_missing_user_raises_invalid_credentials(
    service: AuthService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=None)

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)

    with pytest.raises(InvalidCredentialsError):
        await service.login(email="missing@example.com", password="password123")


@pytest.mark.asyncio
async def test_login_wrong_password_raises_invalid_credentials(
    service: AuthService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=_make_user())
    verify_password_mock = Mock(return_value=False)

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.verify_password",
        verify_password_mock,
    )

    with pytest.raises(InvalidCredentialsError):
        await service.login(email="user@example.com", password="wrong-password")

    get_by_email_mock.assert_awaited_once_with("user@example.com")
    verify_password_mock.assert_called_once_with(
        "wrong-password",
        "hash-password",
    )


@pytest.mark.asyncio
async def test_login_token_error_raises_infrastructure(
    service: AuthService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=_make_user())
    verify_password_mock = Mock(return_value=True)

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.verify_password",
        verify_password_mock,
    )

    def _raise_token_error(user_id: int) -> str:
        raise TokenError("jwt broken")

    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.create_access_token",
        _raise_token_error,
    )

    with pytest.raises(AuthInfrastructureError):
        await service.login(email="user@example.com", password="password123")

    get_by_email_mock.assert_awaited_once_with("user@example.com")
    verify_password_mock.assert_called_once_with("password123", "hash-password")


@pytest.mark.asyncio
async def test_login_does_not_commit(
    service: AuthService,
    session_mock: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_by_email_mock = AsyncMock(return_value=_make_user())
    verify_password_mock = Mock(return_value=True)
    create_access_token_mock = Mock(return_value="token")

    monkeypatch.setattr(service._users, "get_by_email", get_by_email_mock)
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.verify_password",
        verify_password_mock,
    )
    monkeypatch.setattr(
        "services.api_gateway.app.auth.service.create_access_token",
        create_access_token_mock,
    )

    _ = await service.login(email="user@example.com", password="password123")

    get_by_email_mock.assert_awaited_once_with("user@example.com")
    verify_password_mock.assert_called_once_with(
        "password123",
        "hash-password",
    )
    create_access_token_mock.assert_called_once_with(1)
    session_mock.commit.assert_not_awaited()
    session_mock.rollback.assert_not_awaited()
