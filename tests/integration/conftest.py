from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from services.api_gateway.app.settings import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


@pytest.fixture
async def integration_engine() -> AsyncIterator[AsyncEngine]:
    database_url = settings.DATABASE_URL
    if not database_url:
        pytest.fail("DATABASE_URL is required for PostgreSQL integration tests")

    engine = create_async_engine(database_url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def integration_session_factory(
    integration_engine: AsyncEngine,
) -> async_sessionmaker:
    return async_sessionmaker(integration_engine, expire_on_commit=False)


async def _clean_task_data(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        identity = (await connection.execute(text("SELECT current_database(), current_user"))).one()
        if identity != ("todo_test", "todo_test"):
            pytest.fail(
                "Refusing destructive integration cleanup: expected database/user "
                f"todo_test/todo_test, got {identity[0]!r}/{identity[1]!r}"
            )

        await connection.execute(text("TRUNCATE TABLE tasks, users RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
async def clean_task_data(integration_engine: AsyncEngine) -> AsyncIterator[None]:
    await _clean_task_data(integration_engine)
    try:
        yield
    finally:
        await _clean_task_data(integration_engine)
