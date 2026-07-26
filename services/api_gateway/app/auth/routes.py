from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.app.api.deps import get_session
from services.api_gateway.app.auth.dependencies import get_current_user
from services.api_gateway.app.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from services.api_gateway.app.auth.service import (
    AuthInfrastructureError,
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from services.api_gateway.app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, session: SessionDependency) -> UserResponse:
    service = AuthService(session)

    try:
        user = await service.register(
            email=str(payload.email),
            password=payload.password,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc
    except AuthInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return cast(UserResponse, UserResponse.model_validate(user))


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(payload: LoginRequest, session: SessionDependency) -> TokenResponse:
    service = AuthService(session)

    try:
        access_token = await service.login(
            email=str(payload.email),
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc
    except AuthInfrastructureError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        ) from exc

    return TokenResponse(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return cast(UserResponse, UserResponse.model_validate(current_user))
