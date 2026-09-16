"""
Unit & API route tests for Phase 22 Swarm REST endpoints.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db
from src.infrastructure.models.company_model import Base


@pytest.fixture
def client():
    # Use shared in-memory SQLite connection URI for test stability across HTTP requests
    engine = create_async_engine("sqlite+aiosqlite:///file:swarmtestdb?mode=memory&cache=shared&uri=true", echo=False)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    asyncio.run(init_db())

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_swarm_routes_flow(client: TestClient):
    # 1. Create Swarm
    create_res = client.post(
        "/swarms",
        json={
            "parent_task_id": "task-API-100",
            "name": "API Test Swarm",
            "purpose": "Verify REST endpoints",
            "manager_id": "emp-mgr-1",
            "coordination_mode": "PARALLEL",
            "max_agents": 5,
        },
    )
    assert create_res.status_code == 201
    data = create_res.json()
    swarm_id = data["swarm_id"]
    assert swarm_id.startswith("sw_")

    # 2. Get Swarm details
    get_res = client.get(f"/swarms/{swarm_id}")
    assert get_res.status_code == 200
    details = get_res.json()
    assert details["name"] == "API Test Swarm"
    assert details["coordination_mode"] == "PARALLEL"

    # 3. Plan Swarm
    plan_res = client.post(
        f"/swarms/{swarm_id}/plan",
        json={
            "task_title": "API Test Task",
            "task_description": "API Test Description",
            "required_capabilities": ["code_generation", "testing"],
        },
    )
    assert plan_res.status_code == 200
    assert plan_res.json()["status"] == "READY"

    # 4. Start Swarm
    start_res = client.post(f"/swarms/{swarm_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "RUNNING"

    # 5. List Swarms
    list_res = client.get("/swarms")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
