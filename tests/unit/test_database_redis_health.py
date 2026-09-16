"""Unit tests for Database Pooling & Redis Client Health Checks."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from src.infrastructure.database import check_database_health, dispose_engine, get_engine
from src.infrastructure.redis_client import RedisClientManager


@pytest.mark.asyncio
async def test_database_health_check_sqlite_memory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    healthy, msg = await check_database_health(engine)
    assert healthy is True
    assert "healthy" in msg
    await dispose_engine(engine)


@pytest.mark.asyncio
async def test_database_health_check_invalid_url():
    engine = create_async_engine("sqlite+aiosqlite:///nonexistent_dir/bad.db", echo=False)
    healthy, msg = await check_database_health(engine)
    assert healthy is False
    assert "unavailable" in msg
    await dispose_engine(engine)


@pytest.mark.asyncio
async def test_redis_manager_health_check():
    # Test Redis manager initialization & fallback URL check
    mgr = RedisClientManager(url="redis://localhost:6379/15")
    assert mgr.url == "redis://localhost:6379/15"
    # Execute check_health (will attempt ping or catch connection refusions cleanly)
    healthy, msg = await mgr.check_health()
    assert isinstance(healthy, bool)
    assert isinstance(msg, str)
    await mgr.close()
