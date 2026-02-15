from __future__ import annotations

from app.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """
    Репозиторий пользователей (DB-access слой).

    Правила:
    - Никаких HTTPException (это не уровень API).
    - Никаких commit() (commit делает сервис/эндпоинт).
    - Возвращаем модели SQLAlchemy (User) или None.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        if not isinstance(email, str):
            raise TypeError("email must be str")

        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        if not isinstance(id, int):
            raise TypeError("user_id must be int")

        stmt = select(User).where(User.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self, email: str, password_hash: str, username: str | None = None
    ) -> User:
        if not isinstance(email, str):
            raise TypeError("email must be str")
        if not isinstance(password_hash, str):
            raise TypeError("password_hash must be str")
        if username is not None and not isinstance(username, str):
            raise TypeError("username must be str or None")

        user = User(
            email=email,
            password_hash=password_hash,
            username=username,
        )

        self._session.add(user)

        # flush отправляет INSERT в БД, но не коммитит транзакцию.
        # После flush у user появляется id (если PK генерится БД).
        await self._session.flush()

        # refresh подтягивает значения, которые выставляет БД
        # (например created_at через server_default).
        await self._session.refresh(user)

        return user
