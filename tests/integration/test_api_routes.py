"""
Integration tests for FastAPI Runtime API endpoints using httpx AsyncClient.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.application.provider_registry import default_provider_registry
from src.infrastructure.database import Base, get_db_session
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.groq_provider import GroqModelProvider


@pytest.fixture
async def api_client() -> AsyncClient:
    default_provider_registry.register(GroqModelProvider(api_key="gsk_test"))
    default_provider_registry.register(FakeModelProvider())

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
async def test_health_check_endpoint(api_client: AsyncClient) -> None:
    res = await api_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_agent_and_run_api_endpoints(api_client: AsyncClient) -> None:
    # 1. Create Agent via POST /agents
    create_agent_payload = {
        "id": "agent_api_01",
        "name": "API Researcher",
        "role": "researcher",
        "description": "API Test Agent",
        "responsibilities": ["test apis"],
        "capabilities": ["http_testing"],
        "model_configuration": {
            "provider": "fake",
            "model": "fake-model",
            "temperature": 0.5,
        },
        "permission_profile": {"permissions": ["read_all"]},
        "verification_policy": {"required": False},
        "communication_policy": {"allowed_channels": ["chat"]},
    }

    res = await api_client.post("/agents", json=create_agent_payload)
    assert res.status_code == 201, f"Create agent failed: {res.text}"
    agent_data = res.json()
    assert agent_data["id"] == "agent_api_01"
    assert agent_data["current_state"] == "IDLE"

    # 2. Get Agent via GET /agents/{id}
    res = await api_client.get("/agents/agent_api_01")
    assert res.status_code == 200, f"Get agent failed: {res.text}"
    assert res.json()["name"] == "API Researcher"

    # 3. List Agents via GET /agents
    res = await api_client.get("/agents")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 4. Trigger Run via POST /agents/{id}/runs
    run_payload = {
        "objective": "Test runtime API execution flow",
    }
    res = await api_client.post("/agents/agent_api_01/runs", json=run_payload)
    assert res.status_code == 201, f"Create run failed: {res.text}"
    run_data = res.json()
    run_id = run_data["id"]
    assert run_data["status"] == "COMPLETED"
    assert run_data["result"] is not None

    # 5. Get Run via GET /runs/{run_id}
    res = await api_client.get(f"/runs/{run_id}")
    assert res.status_code == 200
    assert res.json()["id"] == run_id

    # 6. List Steps via GET /runs/{run_id}/steps
    res = await api_client.get(f"/runs/{run_id}/steps")
    assert res.status_code == 200
    steps = res.json()
    assert len(steps) == 5

    # 7. List Checkpoints via GET /runs/{run_id}/checkpoints
    res = await api_client.get(f"/runs/{run_id}/checkpoints")
    assert res.status_code == 200
    checkpoints = res.json()
    assert len(checkpoints) >= 1


@pytest.mark.asyncio
async def test_cancel_run_api_endpoint(api_client: AsyncClient) -> None:
    # Create agent
    agent_payload = {
        "id": "agent_api_cancel",
        "name": "Cancel Agent",
        "role": "Worker",
        "model_configuration": {
            "provider": "fake",
            "model": "fake-model",
        },
    }
    create_res = await api_client.post("/agents", json=agent_payload)
    assert create_res.status_code == 201, f"Create agent failed: {create_res.text}"

    # Trigger run
    run_res = await api_client.post(
        "/agents/agent_api_cancel/runs", json={"objective": "To cancel"}
    )
    assert run_res.status_code == 201, f"Trigger run failed: {run_res.text}"
    run_id = run_res.json()["id"]

    # Cancel via POST /runs/{run_id}/cancel
    res = await api_client.post(f"/runs/{run_id}/cancel")
    assert res.status_code == 200
    assert res.json()["id"] == run_id
