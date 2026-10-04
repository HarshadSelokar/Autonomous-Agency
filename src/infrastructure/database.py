"""SQLAlchemy Async Database Setup, Connection Pooling & Health Management."""

import logging
from collections.abc import AsyncGenerator, Callable
from typing import Any, TypeVar

from sqlalchemy import String, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from src.infrastructure.config import settings
from src.infrastructure.tenant_context import install_tenant_scoping

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""

    # Every table is tenant-scoped; see src/infrastructure/tenant_context.py.
    # Models may redeclare the column (e.g. NOT NULL with a foreign key).
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)


install_tenant_scoping(Base)


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

T = TypeVar("T")


async def run_with_sync_session(db: Any, operation: Callable[[Session], T]) -> T:
    """
    Run code written against the synchronous Session API (governance, model routing and
    verification repositories) on the request's AsyncSession.

    AsyncSession.run_sync hands the operation a real sync Session whose I/O is bridged to
    the async driver, so the same repositories work in production and in sync-session tests.
    """
    if isinstance(db, AsyncSession):
        return await db.run_sync(operation)
    return operation(db)


class SyncRepositoryBridge:
    """
    Exposes a repository written for the synchronous Session as awaitable methods on an
    AsyncSession: every call runs the real repository inside AsyncSession.run_sync.

    Callers that already cope with either style (`await res if isawaitable(res) else res`)
    work unchanged. A sync Session is passed straight through.
    """

    def __init__(self, repository_class: type, db: Any) -> None:
        self._repository_class = repository_class
        self._db = db

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") or not callable(getattr(self._repository_class, name, None)):
            raise AttributeError(name)

        if not isinstance(self._db, AsyncSession):
            return getattr(self._repository_class(self._db), name)

        async def call(*args: Any, **kwargs: Any) -> Any:
            return await self._db.run_sync(
                lambda session: getattr(self._repository_class(session), name)(*args, **kwargs)
            )

        return call


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
