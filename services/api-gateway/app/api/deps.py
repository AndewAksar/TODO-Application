from __future__ import annotations

from collections.abc import AsyncGenerator

# SessionLocal — это "фабрика" (sessionmaker), которая создаёт AsyncSession.
# Она уже сконфигурирована в app/db.py через engine = create_async_engine(...).
from app.db import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency: создаёт и отдаёт AsyncSession на время одного запроса.

    Механика работы:
    - Код ДО yield выполняется до запуска endpoint-а.
    - yield отдаёт session в endpoint (или другую dependency).
    - Код ПОСЛЕ yield выполняется после того, как endpoint завершился
      (даже если он завершился исключением).

    Почему используем `async with`:
    - гарантирует session.close() автоматически
    - возвращает соединение в пул
    - защищает от утечек ресурсов
    """
    async with SessionLocal() as session:
        # Здесь мы "передаём" сессию наружу (в FastAPI).
        yield session
