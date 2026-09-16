"""
Integration API tests for Phase 7 Memory, Workspace, and Artifact REST Endpoints.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
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
async def test_memory_api_lifecycle(async_client: AsyncClient) -> None:
    # 1. Create Memory Candidate
    resp = await async_client.post(
        "/memories",
        json={
            "memory_type": "SEMANTIC",
            "scope": "TASK",
            "owner_id": "TASK:T100",
            "content": "PostgreSQL database is configured for production.",
            "summary": "DB config",
            "authority": "GENERATED",
            "confidence": 0.90,
            "provenance": "AGENT_RUN",
            "task_id": "T100",
            "employee_id": "emp-api-dev",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    mem_id = data["id"]
    assert data["authority"] == "GENERATED"
    assert data["status"] == "ACTIVE"

    # 2. List memories
    resp = await async_client.get("/memories", params={"owner_id": "TASK:T100"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 3. Confirm memory
    resp = await async_client.post(
        f"/memories/{mem_id}/confirm",
        json={"actor_employee_id": "emp-api-dev"},
    )
    assert resp.status_code == 200
    assert resp.json()["authority"] == "CONFIRMED"

    # 4. Promote memory by Manager to AUTHORITATIVE
    resp = await async_client.post(
        f"/memories/{mem_id}/promote",
        json={"actor_employee_id": "emp-api-mgr", "target_authority": "AUTHORITATIVE"},
    )
    assert resp.status_code == 200
    assert resp.json()["authority"] == "AUTHORITATIVE"

    # 5. Unauthorized promotion by Dev fails (403)
    resp = await async_client.post(
        f"/memories/{mem_id}/promote",
        json={"actor_employee_id": "emp-api-dev", "target_authority": "AUTHORITATIVE"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_workspace_api_lifecycle(async_client: AsyncClient) -> None:
    # 1. Create Workspace
    resp = await async_client.post(
        "/workspaces",
        json={
            "name": "Research Task Workspace",
            "workspace_type": "TASK",
            "owner_id": "TASK:T100",
            "task_id": "T100",
            "employee_id": "emp-api-dev",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    ws_id = data["id"]
    assert data["status"] == "ACTIVE"

    # 2. Get Workspace
    resp = await async_client.get(f"/workspaces/{ws_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ws_id

    # 3. Lock Workspace
    resp = await async_client.post(f"/workspaces/{ws_id}/lock")
    assert resp.status_code == 200
    assert resp.json()["status"] == "LOCKED"


@pytest.mark.asyncio
async def test_artifact_api_lifecycle_and_versioning(async_client: AsyncClient) -> None:
    # 1. Create Workspace
    ws_resp = await async_client.post(
        "/workspaces",
        json={
            "name": "Artifact Testing Workspace",
            "workspace_type": "TASK",
            "owner_id": "TASK:T200",
            "task_id": "T200",
        },
    )
    ws_id = ws_resp.json()["id"]

    # 2. Create Artifact in Workspace
    resp = await async_client.post(
        f"/workspaces/{ws_id}/artifacts",
        json={
            "name": "architecture.md",
            "mime_type": "text/markdown",
            "content_base64_or_text": "# System Architecture\nInitial Version",
            "created_by_employee_id": "emp-api-dev",
            "task_id": "T200",
        },
    )
    assert resp.status_code == 201
    art_v1 = resp.json()
    art_id = art_v1["id"]
    assert art_v1["version"] == 1
    assert art_v1["checksum_sha256"] != ""

    # 3. Create Version 2 of Artifact
    resp_v2 = await async_client.post(
        f"/artifacts/{art_id}/versions",
        json={
            "name": "architecture.md",
            "mime_type": "text/markdown",
            "content_base64_or_text": "# System Architecture\nUpdated Version 2",
            "created_by_employee_id": "emp-api-dev",
        },
    )
    assert resp_v2.status_code == 200
    art_v2 = resp_v2.json()
    assert art_v2["version"] == 2
    assert art_v2["checksum_sha256"] != art_v1["checksum_sha256"]

    # 4. List artifacts in workspace
    resp_list = await async_client.get(f"/workspaces/{ws_id}/artifacts")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 2
