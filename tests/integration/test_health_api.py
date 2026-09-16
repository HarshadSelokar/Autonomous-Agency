"""Integration tests for Phase 20 Health & Readiness API Endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.database import Base, get_db, get_db_session


@pytest.fixture
async def api_client() -> AsyncClient:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_liveness_endpoint(api_client: AsyncClient):
    res = await api_client.get("/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    # Check correlation ID response header
    assert "X-Request-ID" in res.headers
    assert "X-Correlation-ID" in res.headers


@pytest.mark.asyncio
async def test_readiness_endpoint(api_client: AsyncClient):
    res = await api_client.get("/health/ready")
    assert res.status_code in (200, 503)
    data = res.json()
    assert "status" in data
    assert "dependencies" in data
    assert "metrics_summary" in data
