from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import cast

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config

# Логирование (у тебя в alembic.ini оно есть, так что можно оставлять)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- импортируем настройки/базу/модели приложения ---
import app.models  # noqa: E402,F401  # важно: чтобы модели попали в Base.metadata
from app.db import Base  # noqa: E402
from app.settings import settings  # noqa: E402

target_metadata = Base.metadata


def _get_database_url() -> str:
    # должен быть формата: postgresql+asyncpg://...
    return cast(str, settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Offline: генерируем SQL без подключения к БД."""
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Внутренняя sync-часть: Alembic работает синхронно."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Online: подключаемся к БД через async engine."""
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _get_database_url()

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
