"""
Integration tests for Communication REST API endpoints.
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
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Seed test employees
        emp_repo = SQLAlchemyEmployeeRepository(session)
        await emp_repo.save(
            Employee(
                id="emp-dev",
                employee_code="E1",
                name="Dev Employee",
                title="Developer",
                role="IC",
                agent_id="ag-1",
                status=EmployeeStatus.ACTIVE,
            )
        )
        await emp_repo.save(
            Employee(
                id="emp-mgr",
                employee_code="E2",
                name="Manager Employee",
                title="Engineering Lead",
                role="Manager",
                agent_id="ag-2",
                status=EmployeeStatus.ACTIVE,
            )
        )

        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_communication_api_workflow(async_client: AsyncClient) -> None:
    # 1. Create Conversation
    resp = await async_client.post(
        "/conversations",
        json={
            "title": "Task Discussion",
            "conversation_type": "TASK",
            "created_by_employee_id": "emp-dev",
            "participant_employee_ids": ["emp-mgr"],
            "related_task_id": "task-99",
        },
    )
    assert resp.status_code == 201
    conv_data = resp.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Task Discussion"

    # 2. Send Message
    resp = await async_client.post(
        f"/conversations/{conv_id}/messages",
        json={
            "sender_employee_id": "emp-dev",
            "message_type": "QUESTION",
            "subject": "Architecture question",
            "content": "Should we use asyncpg or psycopg3?",
        },
    )
    assert resp.status_code == 201
    msg_data = resp.json()
    msg_id = msg_data["id"]
    assert msg_data["delivery_state"] == "DELIVERED"

    # 3. List Messages
    resp = await async_client.get(f"/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 1

    # 4. Acknowledge Message
    resp = await async_client.post(
        f"/messages/{msg_id}/acknowledge",
        json={"participant_id": "emp-mgr"},
    )
    assert resp.status_code == 200
    ack_data = resp.json()
    assert ack_data["delivery_state"] == "ACKNOWLEDGED"

    # 5. Report Blocker via Task API endpoint
    resp = await async_client.post(
        "/tasks/task-99/blockers",
        json={
            "sender_employee_id": "emp-dev",
            "blocker_description": "Database connection pool exhausted",
            "manager_employee_id": "emp-mgr",
        },
    )
    assert resp.status_code == 201
    blocker_data = resp.json()
    assert blocker_data["message_type"] == "BLOCKER"
