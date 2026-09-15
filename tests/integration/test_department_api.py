"""Integration tests for Phase 14 Department & Cross-Department API endpoints."""

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
    # 1. Create Department via POST /departments
    create_payload = {
        "id": "dept-api-legal",
        "name": "Legal & Compliance",
        "code": "LEG-API",
        "description": "Legal contract review department",
        "purpose": "Provide legal oversight",
        "capabilities": ["CONTRACT_REVIEW", "COMPLIANCE_ANALYSIS"],
    }
    res = await api_client.post("/departments", json=create_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == "dept-api-legal"
    assert data["status"] == "ACTIVE"

    # 2. List Departments via GET /departments
    res = await api_client.get("/departments")
    assert res.status_code == 200
    depts = res.json()
    assert len(depts) >= 1

    # 3. Get Department by ID via GET /departments/{id}
    res = await api_client.get("/departments/dept-api-legal")
    assert res.status_code == 200
    assert res.json()["name"] == "Legal & Compliance"

    # 4. Update Status via POST /departments/{id}/status
    res = await api_client.post("/departments/dept-api-legal/status", json={"status": "PAUSED", "reason": "Audit"})
    assert res.status_code == 200
    assert res.json()["status"] == "PAUSED"


@pytest.mark.asyncio
async def test_bootstrap_departments_api(api_client: AsyncClient):
    res = await api_client.post("/departments/bootstrap")
    assert res.status_code == 200
    depts = res.json()
    assert len(depts) >= 13


@pytest.mark.asyncio
async def test_cross_department_request_api_flow(api_client: AsyncClient):
    # 1. Bootstrap departments
    await api_client.post("/departments/bootstrap")

    # 2. Submit Request via POST /department-requests
    req_payload = {
        "requester_department_id": "dept-prod",
        "receiving_department_id": "dept-eng",
        "requester_employee_id": "emp-prod-lead",
        "purpose": "Build authentication module",
        "requested_outcome": "OAuth2 endpoints ready",
        "priority": "HIGH",
    }
    res = await api_client.post("/department-requests", json=req_payload)
    assert res.status_code == 201
    req_data = res.json()
    req_id = req_data["request_id"]
    assert req_data["status"] == "REQUESTED"

    # 3. Accept Request via POST /department-requests/{id}/accept
    accept_payload = {
        "receiving_manager_id": "emp-eng-mgr",
        "delivery_owner_employee_id": "emp-dev-lead",
    }
    res = await api_client.post(f"/department-requests/{req_id}/accept", json=accept_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ACCEPTED"

    # 4. Submit Handoff via POST /department-requests/{id}/handoff
    handoff_payload = {
        "sender_employee_id": "emp-dev-lead",
        "expected_outcome": "OAuth2 endpoints deployed",
        "artifact_ids": ["art-oauth-spec"],
    }
    res = await api_client.post(f"/department-requests/{req_id}/handoff", json=handoff_payload)
    assert res.status_code == 201
    handoff_data = res.json()
    handoff_id = handoff_data["handoff_id"]
    assert handoff_data["status"] == "PROPOSED"

    # 5. Verify Handoff via POST /department-requests/handoffs/{id}/verify
    verify_payload = {
        "verifier_employee_id": "emp-prod-lead",
        "is_approved": True,
    }
    res = await api_client.post(f"/department-requests/handoffs/{handoff_id}/verify", json=verify_payload)
    assert res.status_code == 200
    assert res.json()["is_verified"] is True
