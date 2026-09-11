"""
SQLAlchemy Async Database Setup & Session Management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.config import settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""

    pass


# Create async engine
def get_engine(url: str | None = None) -> AsyncEngine:
    db_url = url or settings.DATABASE_URL
    return create_async_engine(
        db_url,
        echo=settings.DATABASE_ECHO,
        future=True,
    )


engine = get_engine()
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper for acquiring async DB sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
