"""Integration tests for Phase 15 Workforce and Teams REST APIs."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.infrastructure.database import Base, get_db_session


@pytest.fixture
def client_and_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    asyncio.run(_setup_tables())

    async def _override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_workforce_demand_api_flow(client_and_session):
    client = client_and_session

    # 1. Create demand
    resp = client.post(
        "/workforce/demands",
        json={
            "source_type": "PROJECT",
            "source_id": "proj-phoenix",
            "capability": "BACKEND_DEVELOPMENT",
            "required_count": 2,
            "priority": 4,
        },
    )
    assert resp.status_code == 201
    demand_data = resp.json()
    assert demand_data["capability"] == "BACKEND_DEVELOPMENT"
    demand_id = demand_data["id"]

    # 2. List demands
    resp_list = client.get("/workforce/demands")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1

    # 3. Detect gaps
    resp_gaps = client.get("/workforce/gaps")
    assert resp_gaps.status_code == 200
    gaps = resp_gaps.json()
    assert len(gaps) >= 1
    assert gaps[0]["capability"] == "BACKEND_DEVELOPMENT"

    # 4. Generate recommendation
    resp_rec = client.post("/workforce/recommendations", json={"demand_id": demand_id})
    assert resp_rec.status_code == 201
    assert "demand_id" in resp_rec.json()

    # 5. Workforce health
    resp_health = client.get("/workforce/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] in ("HEALTHY", "CAPABILITY_CONSTRAINED")


def test_teams_api_flow(client_and_session):
    client = client_and_session

    # 1. Create team
    resp = client.post(
        "/teams",
        json={
            "name": "Alpha Squad",
            "code": "SQD-A",
            "purpose": "Backend Overhaul",
            "team_type": "PROJECT",
        },
    )
    assert resp.status_code == 201
    team_data = resp.json()
    assert team_data["code"] == "SQD-A"
    team_id = team_data["id"]

    # 2. Get team
    resp_get = client.get(f"/teams/{team_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["name"] == "Alpha Squad"

    # 3. Dissolve team
    resp_dis = client.post(f"/teams/{team_id}/dissolve")
    assert resp_dis.status_code == 200
    assert resp_dis.json()["status"] == "DISSOLVED"
