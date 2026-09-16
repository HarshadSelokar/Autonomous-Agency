from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.models  # noqa: F401
from src.api.main import app
from src.infrastructure.database import Base, get_db
from src.infrastructure.models.objective_model import ObjectiveModel
from src.infrastructure.models.plan_model import PlanModel


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Pre-populate dummy Objective and Plan
        obj = ObjectiveModel(
            id="obj-1",
            title="API Test Obj",
            description="Desc",
            requester="User",
            status="APPROVED",
            constraints_json=[],
            metadata_json={},
        )
        plan = PlanModel(
            id="plan-1",
            objective_id="obj-1",
            manager_id="mgr-1",
            assumptions_json=[],
            goals_json=[],
            required_capabilities_json=[],
            risks_json=[],
            constraints_json=[],
            status="APPROVED",
            metadata_json={},
        )
        session.add(obj)
        session.add(plan)
        await session.commit()

        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_get_list_tasks_api(async_client: AsyncClient) -> None:
    # 1. Create Task
    resp = await async_client.post(
        "/tasks",
        json={
            "plan_id": "plan-1",
            "title": "API Build Task",
            "description": "Building FastAPI routes",
            "priority": "high",
            "required_capabilities": ["fastapi", "python"],
        },
    )
    assert resp.status_code == 201
    task_data = resp.json()
    task_id = task_data["id"]
    assert task_data["title"] == "API Build Task"
    assert task_data["status"] in {"CREATED", "READY"}

    # 2. Get Task by ID
    resp = await async_client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id

    # 3. List Tasks
    resp = await async_client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_add_dependency_and_cycle_rejection_api(async_client: AsyncClient) -> None:
    # Create Task 1
    resp1 = await async_client.post(
        "/tasks",
        json={"plan_id": "plan-1", "title": "Task A", "description": "Desc A"},
    )
    t1_id = resp1.json()["id"]

    # Create Task 2
    resp2 = await async_client.post(
        "/tasks",
        json={"plan_id": "plan-1", "title": "Task B", "description": "Desc B"},
    )
    t2_id = resp2.json()["id"]

    # Add Dependency: T1 -> T2
    resp_dep = await async_client.post(
        f"/tasks/{t2_id}/dependencies",
        json={"predecessor_task_id": t1_id, "successor_task_id": t2_id},
    )
    assert resp_dep.status_code == 201

    # Attempt Cycle: T2 -> T1
    resp_cycle = await async_client.post(
        f"/tasks/{t1_id}/dependencies",
        json={"predecessor_task_id": t2_id, "successor_task_id": t1_id},
    )
    assert resp_cycle.status_code == 400
    assert "cycle" in resp_cycle.json()["detail"].lower()


@pytest.mark.asyncio
async def test_scheduler_run_api(async_client: AsyncClient) -> None:
    resp = await async_client.post("/scheduler/run", json={"worker_id": "worker-api-1", "max_tasks": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "processed_tasks" in data
