from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.app.api.deps import get_session
from services.api_gateway.app.models import User
from services.api_gateway.app.repositories.users import UserRepository
from services.api_gateway.app.security.jwt import TokenError, decode_token

UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized",
)


SERVICE_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Service temporarily unavailable",
)


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise UNAUTHORIZED

    try:
        decoded = decode_token(credentials.credentials)
    except TokenError as exc:
        raise UNAUTHORIZED from exc

    repo = UserRepository(session)
    try:
        user = await repo.get_by_id(decoded.user_id)
    except SQLAlchemyError as exc:
        raise SERVICE_UNAVAILABLE from exc

    if user is None:
        raise UNAUTHORIZED

    return user
