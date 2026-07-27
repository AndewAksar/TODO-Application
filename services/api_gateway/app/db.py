from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from services.api_gateway.app.settings import settings


class Base(DeclarativeBase):
    pass


def _require_database_url() -> str:
    url = settings.DATABASE_URL
    if not url or not url.strip():
        raise RuntimeError("DATABASE_URL is required")
    return url


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_async_engine(_require_database_url(), echo=False)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker:
    return async_sessionmaker(get_engine(), expire_on_commit=False)
