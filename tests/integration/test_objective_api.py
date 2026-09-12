"""
Integration tests for Objective & Manager Orchestration REST API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.application.provider_registry import default_provider_registry
from src.infrastructure.database import Base, get_db_session
from src.infrastructure.models.fake_provider import FakeModelProvider


@pytest.fixture
async def api_client() -> AsyncClient:
    default_provider_registry.register(
        FakeModelProvider(
            canned_content="Manager Output: Objective analyzed and planned successfully."
        )
    )

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
async def test_objective_api_flow(api_client: AsyncClient) -> None:
    # 1. Create backing Agent & Manager Employee
    agent_res = await api_client.post(
        "/agents",
        json={
            "id": "ag_mgr_api",
            "name": "Manager Agent",
            "role": "manager",
            "model_configuration": {"provider": "fake", "model": "fake-model"},
        },
    )
    assert agent_res.status_code == 201

    emp_res = await api_client.post(
        "/employees",
        json={
            "id": "emp_bob_api",
            "employee_code": "EMP-BOB-API",
            "name": "Bob Manager",
            "title": "Engineering Manager",
            "role": "engineering_manager",
            "agent_id": "ag_mgr_api",
            "capabilities": [{"name": "planning", "description": "Plan projects"}],
        },
    )
    assert emp_res.status_code == 201

    # Activate Manager
    status_res = await api_client.post(
        "/employees/emp_bob_api/status", json={"status": "ACTIVE"}
    )
    assert status_res.status_code == 200

    # 2. Create Objective via POST /objectives
    obj_payload = {
        "id": "obj_analytics_api",
        "title": "Build CSV Analytics",
        "description": "Parse CSV files and render charts",
        "requester": "VP Product",
        "priority": "high",
        "constraints": ["python3.11"],
        "manager_id": "emp_bob_api",
    }
    res = await api_client.post("/objectives", json=obj_payload)
    assert res.status_code == 201
    assert res.json()["status"] == "RECEIVED"

    # 3. Get Objective via GET /objectives/{id}
    res = await api_client.get("/objectives/obj_analytics_api")
    assert res.status_code == 200
    assert res.json()["title"] == "Build CSV Analytics"

    # 4. Request & Provide Clarification
    res = await api_client.post(
        "/objectives/obj_analytics_api/clarify-request",
        json={"questions": ["Input CSV format?"]},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CLARIFICATION_REQUIRED"

    res = await api_client.post(
        "/objectives/obj_analytics_api/clarify-answers",
        json={"answers": {"Input CSV format?": "Standard comma-separated"}},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "READY_FOR_PLANNING"

    # 5. Submit Plan via POST /objectives/{id}/plan
    plan_payload = {
        "id": "plan_analytics_api",
        "objective_id": "obj_analytics_api",
        "manager_id": "emp_bob_api",
        "goals": ["Build analytics app"],
        "work_items": [
            {
                "id": "wi_api_01",
                "title": "Build Parser API",
                "description": "Write CSV parser module",
                "required_capabilities": ["python"],
            }
        ],
    }
    res = await api_client.post("/objectives/obj_analytics_api/plan", json=plan_payload)
    assert res.status_code == 201
    assert res.json()["status"] == "PROPOSED"

    # 6. Approve Plan via POST /objectives/plans/{id}/approve
    res = await api_client.post(
        "/objectives/plans/plan_analytics_api/approve",
        params={"manager_id": "emp_bob_api"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 7. Execute Manager Run via POST /objectives/{id}/runs
    res = await api_client.post(
        "/objectives/obj_analytics_api/runs",
        params={"manager_id": "emp_bob_api"},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "COMPLETED"
