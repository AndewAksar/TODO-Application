from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt

from services.api_gateway.app.settings import settings


# ---- Domain-level error (not HTTP) ----
class TokenError(Exception):
    """Любая ошибка валидации/декодирования JWT."""


@dataclass(frozen=True)
class DecodedToken:
    user_id: int
    iat: int
    exp: int


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _require_secret_key() -> str:
    secret = settings.JWT_SECRET_KEY
    if not secret:
        raise TokenError("JWT_SECRET_KEY is not set")
    return secret


def create_access_token(user_id: int) -> str:
    if not isinstance(user_id, int):
        raise TypeError("user_id must be int")

    now = _now_utc()
    iat = int(now.timestamp())

    expires = timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    exp = int((now + expires).timestamp())

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": iat,
        "exp": exp,
    }

    token = jwt.encode(
        payload,
        _require_secret_key(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return cast(str, token)


def decode_token(token: str) -> DecodedToken:
    if not isinstance(token, str):
        raise TypeError("token must be str")
    if token == "":
        raise TokenError("token is empty")

    try:
        payload = jwt.decode(
            token,
            _require_secret_key(),
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise TokenError("invalid token") from e

    sub = payload.get("sub")
    iat = payload.get("iat")
    exp = payload.get("exp")

    if not isinstance(sub, str) or not sub.isdigit():
        raise TokenError("invalid sub")

    if not isinstance(iat, int) or not isinstance(exp, int):
        raise TokenError("invalid iat/exp")

    return DecodedToken(user_id=int(sub), iat=iat, exp=exp)
