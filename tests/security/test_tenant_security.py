"""
Security tests for Tenant isolation and context propagation (Phase 32).
"""

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
async def test_tenant_context_middleware_header_extraction(api_client: AsyncClient):
    headers = {
        "X-Tenant-ID": "tenant-sec-123",
        "X-Tenant-Slug": "sec-tenant",
    }
    res = await api_client.get("/health/live", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("X-Tenant-ID") == "tenant-sec-123"


@pytest.mark.asyncio
async def test_cross_tenant_isolation_prevention(api_client: AsyncClient):
    # Create Tenant A
    res_a = await api_client.post("/tenants", json={"name": "Tenant Alpha", "slug": "tenant-alpha"})
    assert res_a.status_code == 201
    tenant_a_id = res_a.json()["id"]

    # Create Tenant B
    res_b = await api_client.post("/tenants", json={"name": "Tenant Beta", "slug": "tenant-beta"})
    assert res_b.status_code == 201
    tenant_b_id = res_b.json()["id"]

    # Acting as Tenant B, Tenant A's row does not exist
    headers_b = {"X-Tenant-ID": tenant_b_id}
    res_get = await api_client.get(f"/tenants/{tenant_a_id}", headers=headers_b)
    assert res_get.status_code == 404

    # Tenant B still reads its own row
    res_own = await api_client.get(f"/tenants/{tenant_b_id}", headers=headers_b)
    assert res_own.status_code == 200
    assert res_own.json()["id"] == tenant_b_id
    assert res_own.headers.get("X-Tenant-ID") == tenant_b_id
