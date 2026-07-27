from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from services.api_gateway.app.models import User
from services.api_gateway.app.repositories.users import UserRepository
from services.api_gateway.app.security.jwt import TokenError, create_access_token
from services.api_gateway.app.security.passwords import hash_password, verify_password


class AuthServiceError(Exception):
    """Base auth service exception."""


class EmailAlreadyRegisteredError(AuthServiceError):
    """Raised when email is already registered."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when credentials are invalid."""


class AuthInfrastructureError(AuthServiceError):
    """Raised for infrastructure-level auth failures."""


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(
        self,
        *,
        email: str,
        password: str,
        username: str | None = None,
    ) -> User:
        try:
            existing = await self._users.get_by_email(email)
            if existing is not None:
                raise EmailAlreadyRegisteredError("email already registered")

            password_hash = hash_password(password)

            user = await self._users.create_user(
                email=email,
                password_hash=password_hash,
                username=username,
            )
            await self._session.commit()
            return user

        except EmailAlreadyRegisteredError:
            raise
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError("email already registered") from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise AuthInfrastructureError("database operation failed") from exc

    async def login(self, *, email: str, password: str) -> str:
        try:
            user = await self._users.get_by_email(email)
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise AuthInfrastructureError("database operation failed") from exc

        if user is None:
            raise InvalidCredentialsError("invalid credentials")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("invalid credentials")

        try:
            return create_access_token(user.id)
        except TokenError as exc:
            raise AuthInfrastructureError("token creation failed") from exc
