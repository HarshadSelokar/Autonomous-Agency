"""Integration tests for Phase 14 Department and Cross-Department Request APIs."""

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
async def test_department_api_crud(api_client: AsyncClient):
    payload = {
        "id": "dept-fin-api",
        "name": "Finance",
        "code": "FIN-API",
        "description": "Financial Management",
        "purpose": "Manage corporate budget and analysis",
        "responsibilities": ["budgeting"],
        "capabilities": ["FINANCIAL_ANALYSIS"],
    }

    res = await api_client.post("/departments", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["id"] == "dept-fin-api"
    assert data["code"] == "FIN-API"

    res = await api_client.get("/departments/dept-fin-api")
    assert res.status_code == 200
    assert res.json()["name"] == "Finance"

    res = await api_client.get("/departments")
    assert res.status_code == 200
    assert len(res.json()) >= 1


@pytest.mark.asyncio
async def test_cross_department_request_api_flow(api_client: AsyncClient):
    # 1. Create two departments
    await api_client.post(
        "/departments",
        json={"id": "dept-prod-api", "name": "Product", "code": "PROD-API"},
    )
    await api_client.post(
        "/departments",
        json={"id": "dept-eng-api", "name": "Engineering", "code": "ENG-API"},
    )

    # 2. Create Cross-Department Request
    req_payload = {
        "receiving_department_id": "dept-eng-api",
        "requester_employee_id": "emp-prod-mgr",
        "purpose": "Build Search API",
        "requested_outcome": "Working REST endpoint",
        "priority": "HIGH",
    }
    res = await api_client.post("/departments/dept-prod-api/requests", json=req_payload)
    assert res.status_code == 201, res.text
    req_data = res.json()
    req_id = req_data["request_id"]
    assert req_data["status"] == "REQUESTED"

    # 3. Accept Request
    res = await api_client.post(
        f"/department-requests/{req_id}/accept",
        json={"receiving_manager_id": "emp-eng-mgr", "delivery_owner_employee_id": "emp-dev"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ACCEPTED"
