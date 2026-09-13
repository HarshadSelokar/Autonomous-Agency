"""
Integration API tests for Phase 8 Tool REST Endpoints.
"""

from typing import AsyncGenerator
from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.domain.employee import Employee, EmployeeStatus
from src.infrastructure.database import Base, get_db
from src.infrastructure.models.employee_model import employee_domain_to_model


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    # Seed required employees
    async with async_session_factory() as session:
        emp_mgr = Employee(
            id="emp-api-mgr",
            name="Alice Manager",
            role="Engineering Manager",
            status=EmployeeStatus.ACTIVE,
            employee_code="EMP_API_MGR",
            title="Engineering Manager",
            agent_id="agent-mgr",
        )
        emp_dev = Employee(
            id="emp-api-dev",
            name="Bob Developer",
            role="Software Engineer",
            status=EmployeeStatus.ACTIVE,
            employee_code="EMP_API_DEV",
            title="Senior Developer",
            agent_id="agent-dev",
        )
        session.add(employee_domain_to_model(emp_mgr))
        session.add(employee_domain_to_model(emp_dev))
        await session.commit()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_tool_registration_and_list_api(async_client: AsyncClient) -> None:
    # 1. Register Tool
    resp = await async_client.post(
        "/tools",
        json={
            "id": "file_reader_api_test",
            "name": "API File Reader",
            "description": "Reads workspace files",
            "category": "FILESYSTEM",
            "capabilities": ["READ_FILE"],
            "permission_mode": "AUTO",
            "risk_level": "LOW",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "file_reader_api_test"
    assert data["permission_mode"] == "AUTO"

    # 2. List tools
    resp_list = await async_client.get("/tools")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1


@pytest.mark.asyncio
async def test_tool_execution_api_flow(async_client: AsyncClient) -> None:
    # 1. Register Tool
    await async_client.post(
        "/tools",
        json={
            "id": "comm_message_tool",
            "name": "Communication Message Tool",
            "description": "Sends messages",
            "category": "COMMUNICATION",
            "capabilities": ["SEND_MESSAGE"],
            "permission_mode": "APPROVAL",
            "risk_level": "HIGH",
        },
    )

    # 2. Execute Tool Request -> Enters PENDING_APPROVAL (202 Accepted)
    resp = await async_client.post(
        "/tool-executions",
        json={
            "tool_id": "comm_message_tool",
            "capability": "SEND_MESSAGE",
            "arguments": {"recipient_id": "emp-api-mgr", "content": "Need budget"},
            "employee_id": "emp-api-dev",
            "agent_id": "agent-dev",
            "agent_run_id": "run-api-1",
        },
    )
    assert resp.status_code == 202
    exec_data = resp.json()
    assert exec_data["status"] == "PENDING_APPROVAL"
    approval_id = exec_data["output"]["approval_id"]

    # 3. Manager Approves Request
    appr_resp = await async_client.post(
        f"/tool-approvals/{approval_id}/approve",
        json={"approver_employee_id": "emp-api-mgr", "rationale": "Budget granted"},
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"
