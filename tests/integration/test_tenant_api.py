"""
Integration tests for Tenant API endpoints and repository persistence (Phase 32).
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
async def test_tenant_api_crud_flow(api_client: AsyncClient):
    # 1. Create Tenant
    payload = {
        "name": "Beta Startup",
        "slug": "beta-startup",
        "plan": "PRO",
        "configuration": {
            "max_users": 50,
            "max_projects": 25,
        }
    }
    res = await api_client.post("/tenants", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["slug"] == "beta-startup"
    assert data["plan"] == "PRO"
    assert data["configuration"]["max_users"] == 50
    tenant_id = data["id"]

    # 2. Get Tenant
    res_get = await api_client.get(f"/tenants/{tenant_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Beta Startup"

    # 3. List Tenants
    res_list = await api_client.get("/tenants")
    assert res_list.status_code == 200
    tenants = res_list.json()
    assert any(t["id"] == tenant_id for t in tenants)

    # 4. Patch Tenant Plan
    res_patch = await api_client.patch(f"/tenants/{tenant_id}", json={"plan": "ENTERPRISE"})
    assert res_patch.status_code == 200
    assert res_patch.json()["plan"] == "ENTERPRISE"

    # 5. Delete Tenant
    res_del = await api_client.delete(f"/tenants/{tenant_id}")
    assert res_del.status_code == 204
