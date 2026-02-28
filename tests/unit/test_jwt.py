from typing import cast

import pytest
from jose import jwt
from services.api_gateway.app.security.jwt import TokenError, create_access_token, decode_token
from services.api_gateway.app.settings import settings

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def jwt_test_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-secret-key", raising=True)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256", raising=True)


def _encode_token(payload: dict[str, object]) -> str:
    return cast(
        str,
        jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        ),
    )


def test_create_access_token_then_decode_returns_user_id() -> None:
    token = create_access_token(123)

    decode = decode_token(token)

    assert decode.user_id == 123


def test_decode_token_raises_token_error_for_non_jwt_string() -> None:
    with pytest.raises(TokenError):
        decode_token("not-a-jwt")


def test_decode_token_raises_token_error_when_sub_missing() -> None:
    token_without_sub = _encode_token(
        {
            "iat": 1,
            "exp": 1234567890,
        }
    )
    with pytest.raises(TokenError):
        decode_token(token_without_sub)


def test_decode_token_raises_token_error_when_sub_not_numeric() -> None:
    token_with_invalid_sub = _encode_token(
        {
            "sub": "abc",
            "iat": 1,
            "exp": 1234567890,
        }
    )
    with pytest.raises(TokenError):
        decode_token(token_with_invalid_sub)


def test_decode_token_raises_token_for_expired_token() -> None:
    expired_token = _encode_token(
        {
            "sub": "123",
            "iat": 1,
            "exp": 2,
        }
    )
    with pytest.raises(TokenError):
        decode_token(expired_token)
