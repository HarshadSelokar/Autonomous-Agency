"""SQLAlchemy Async Database Setup, Connection Pooling & Health Management."""

import logging
from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


def get_engine(url: str | None = None) -> AsyncEngine:
    """Create and configure async database engine with production pooling settings."""
    db_url = url or settings.DATABASE_URL
    is_sqlite = "sqlite" in db_url.lower()

    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    if not is_sqlite:
        engine_kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,
        })

    return create_async_engine(db_url, **engine_kwargs)


engine = get_engine()
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper for acquiring async DB sessions with transaction management."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


get_db = get_db_session


async def check_database_health(target_engine: AsyncEngine | None = None) -> tuple[bool, str]:
    """Evaluates database connection health by executing a lightweight ping query."""
    eng = target_engine or engine
    try:
        async with eng.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "Database connection healthy"
    except Exception as err:
        logger.warning(f"Database health check failed: {err}")
        return False, f"Database unavailable: {str(err)}"


async def dispose_engine(target_engine: AsyncEngine | None = None) -> None:
    """Safely disposes database connection pool during application shutdown."""
    eng = target_engine or engine
    logger.info("Disposing database connection pool...")
    await eng.dispose()
