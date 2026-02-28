from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from services.api_gateway.app.settings import settings


class Base(DeclarativeBase):
    pass


if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
    raise RuntimeError("DATABASE_URL is required to initialize database engine")


engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
