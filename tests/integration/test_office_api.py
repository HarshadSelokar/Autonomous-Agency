"""Integration tests for Phase 13 Pixel Office API routes."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.database import Base, get_db_session


@pytest.fixture
async def api_client() -> AsyncClient:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_company_overview(api_client: AsyncClient):
    response = await api_client.get("/office/overview")
    assert response.status_code == 200
    data = response.json()
    assert "company_name" in data
    assert data["company_name"] == "Autonomous AI Organization"
    assert "active_employees_count" in data


@pytest.mark.asyncio
async def test_list_workstations(api_client: AsyncClient):
    response = await api_client.get("/office/employees")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_attention_queue(api_client: AsyncClient):
    response = await api_client.get("/office/attention")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_reconcile_state(api_client: AsyncClient):
    response = await api_client.get("/office/reconcile")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RECONCILED"
