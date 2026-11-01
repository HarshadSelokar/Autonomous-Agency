"""
The governance, model-routing and verification repositories use the synchronous Session
API. These tests run their routes against a real AsyncSession, the way production does,
rather than against a sync session substituted by the test.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.database import Base, get_db_session


@pytest.fixture
async def client() -> AsyncClient:
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_governance_approval_lifecycle_persists(client: AsyncClient):
    created = await client.post(
        "/governance/approvals",
        json={
            "action_type": "DEPLOY",
            "action_target": "production",
            "requested_by_actor_id": "emp-1",
            "risk_level": "HIGH",
        },
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["request_id"]
    assert created.json()["status"] == "PENDING"

    # A separate request (separate session) sees the committed row
    pending = await client.get("/governance/approvals", params={"status": "pending"})
    assert [r["request_id"] for r in pending.json()] == [request_id]

    approved = await client.post(f"/governance/approvals/{request_id}/approve", json={"actor_id": "human-1"})
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED"
    assert approved.json()["approved_by_actor_id"] == "human-1"

    assert (await client.get("/governance/approvals", params={"status": "pending"})).json() == []
    missing = await client.post("/governance/approvals/no-such-id/approve", json={"actor_id": "human-1"})
    assert missing.status_code == 400


async def test_governance_emergency_stop_and_violations(client: AsyncClient):
    stop = await client.post(
        "/governance/stop",
        json={"scope": "GLOBAL", "scope_id": "GLOBAL", "activated_by_actor_id": "human-1", "reason": "test"},
    )
    assert stop.status_code == 200, stop.text
    assert stop.json()["status"] == "ACTIVATED"
    assert (await client.get("/governance/violations")).status_code == 200


async def test_model_routing_register_and_route(client: AsyncClient):
    registered = await client.post(
        "/models",
        json={
            "model_id": "m-fast",
            "provider_name": "groq",
            "model_name": "llama-3.3-70b-versatile",
            "capabilities": ["TEXT_GENERATION"],
        },
    )
    assert registered.status_code == 201, registered.text

    routed = await client.post(
        "/models/route", json={"required_capabilities": ["TEXT_GENERATION"], "strategy": "CAPABILITY_BASED"}
    )
    assert routed.status_code == 200, routed.text
    assert routed.json()["selected_model_id"] == "m-fast"
    assert routed.json()["selected_provider_name"] == "groq"


async def test_verification_outcome_and_lookup(client: AsyncClient):
    outcome = await client.post(
        "/verifications/outcomes",
        json={"task_id": "task-1", "description": "It works", "criteria": ["tests pass"], "rules": []},
    )
    assert outcome.status_code == 201, outcome.text
    assert outcome.json()["task_id"] == "task-1"

    assert (await client.get("/verifications/does-not-exist")).status_code == 404
