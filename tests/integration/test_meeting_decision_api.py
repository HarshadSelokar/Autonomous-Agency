"""
Integration API tests for Meetings and Decisions REST Endpoints.
"""

from datetime import UTC, datetime, timedelta
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
async def test_meeting_api_lifecycle(async_client: AsyncClient) -> None:
    # 1. Create Meeting
    resp = await async_client.post(
        "/meetings",
        json={
            "title": "API Architecture Sync",
            "purpose": "REVIEW",
            "organizer_employee_id": "emp-api-mgr",
            "participant_ids": ["emp-api-dev"],
        },
    )
    assert resp.status_code == 201
    mtg_data = resp.json()
    mtg_id = mtg_data["id"]
    assert mtg_data["status"] == "PROPOSED"
    assert mtg_data["participant_count"] == 2

    # 2. Schedule Meeting
    now = datetime.now(UTC)
    resp = await async_client.post(
        f"/meetings/{mtg_id}/schedule",
        json={
            "scheduled_start": (now + timedelta(hours=1)).isoformat(),
            "scheduled_end": (now + timedelta(hours=2)).isoformat(),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SCHEDULED"

    # 3. Start Meeting
    resp = await async_client.post(f"/meetings/{mtg_id}/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"

    # 4. Get Meeting Context
    resp = await async_client.get(
        f"/meetings/{mtg_id}/context",
        params={"requesting_employee_id": "emp-api-dev"},
    )
    assert resp.status_code == 200
    assert "framed_prompt_context" in resp.json()

    # 5. End Meeting
    resp = await async_client.post(f"/meetings/{mtg_id}/end")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ENDED"


@pytest.mark.asyncio
async def test_decision_api_lifecycle_and_approval(async_client: AsyncClient) -> None:
    # 1. Create Decision Proposal
    resp = await async_client.post(
        "/decisions",
        json={
            "title": "Select Storage System",
            "question": "Which database engine to use?",
            "decision_maker_employee_id": "emp-api-dev",
            "decision_type": "ARCHITECTURE",
            "approving_authority_role": "Engineering Manager",
            "chosen_option": "PostgreSQL",
            "alternatives": ["MongoDB", "Cassandra"],
            "rationale": "PostgreSQL provides ACID compliance.",
        },
    )
    assert resp.status_code == 201
    dec_data = resp.json()
    dec_id = dec_data["id"]
    assert dec_data["status"] == "PROPOSED"

    # 2. Unauthorized Employee Approval Fails (403)
    resp = await async_client.post(
        f"/decisions/{dec_id}/approve",
        json={"approver_employee_id": "emp-api-dev"},
    )
    assert resp.status_code == 403

    # 3. Authorized Manager Approval Succeeds (200)
    resp = await async_client.post(
        f"/decisions/{dec_id}/approve",
        json={"approver_employee_id": "emp-api-mgr"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"
    assert resp.json()["approved_at"] is not None
