from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

# SessionLocal — это "фабрика" (sessionmaker), которая создаёт AsyncSession.
# Она уже сконфигурирована в services/api_gateway/app/db.py через engine = create_async_engine(...).
from services.api_gateway.app.db import SessionLocal


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
