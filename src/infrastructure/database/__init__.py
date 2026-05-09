import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:root@localhost:5433/feedtrade",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # → True en dev
    pool_size=5,  # + Connexions pool
    max_overflow=2,  # + Overflow
    pool_pre_ping=True,  # + Ping avant utilisation (anti-conn mortes)
    pool_recycle=3600,  # + Recycle 1h
)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # + Pas d'auto-flush (contrôle précis)
)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
