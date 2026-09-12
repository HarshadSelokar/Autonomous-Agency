"""
Integration tests for Employee API endpoints using httpx AsyncClient.
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
            canned_content="Employee Work Output: Completed employee task successfully."
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
async def test_employee_api_full_flow(api_client: AsyncClient) -> None:
    # 1. Create backing Agent first via POST /agents
    agent_payload = {
        "id": "agent_emp_01",
        "name": "Employee Agent",
        "role": "researcher",
        "model_configuration": {
            "provider": "fake",
            "model": "fake-model",
        },
    }
    res = await api_client.post("/agents", json=agent_payload)
    assert res.status_code == 201, f"Failed to create agent: {res.text}"

    # 2. Create Employee via POST /employees
    create_emp_payload = {
        "id": "emp_alice_api",
        "employee_code": "EMP-API-001",
        "name": "Alice API",
        "title": "Senior AI Architect",
        "role": "architect",
        "agent_id": "agent_emp_01",
        "responsibilities": ["Design system architecture"],
        "skills": [{"name": "python", "category": "programming", "proficiency": "expert"}],
        "capabilities": [
            {"name": "architecture_design", "description": "Design backend architecture"}
        ],
    }

    res = await api_client.post("/employees", json=create_emp_payload)
    assert res.status_code == 201, f"Failed to create employee: {res.text}"
    emp_data = res.json()
    assert emp_data["id"] == "emp_alice_api"
    assert emp_data["status"] == "INACTIVE"

    # 3. Get Employee via GET /employees/{id}
    res = await api_client.get("/employees/emp_alice_api")
    assert res.status_code == 200
    assert res.json()["name"] == "Alice API"

    # 4. List Employees via GET /employees
    res = await api_client.get("/employees")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 5. Attempt work execution while INACTIVE (expect 400 Bad Request)
    work_payload = {"objective": "Draft Phase 2 architecture specification"}
    res = await api_client.post("/employees/emp_alice_api/runs", json=work_payload)
    assert res.status_code == 400
    assert "is in status 'INACTIVE' and is not authorized" in res.json()["detail"]

    # 6. Activate Employee via POST /employees/{id}/status
    res = await api_client.post("/employees/emp_alice_api/status", json={"status": "ACTIVE"})
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVE"

    # 7. Execute work successfully while ACTIVE
    res = await api_client.post("/employees/emp_alice_api/runs", json=work_payload)
    assert res.status_code == 201, f"Execute work failed: {res.text}"
    run_data = res.json()
    assert run_data["status"] == "COMPLETED"
    assert "Completed employee task successfully" in run_data["result"]["content"]
