"""
Unit tests for Phase 25 Multi-Company & Simulation REST API Endpoints.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db, Base
import src.infrastructure.models.company_model


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:companytestdb?mode=memory&cache=shared&uri=true", echo=False)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_db())

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_list_companies_route(client: TestClient):
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_company_route(client: TestClient):
    payload = {
        "name": "Starlight Autonomous Robotics",
        "slug": "starlight-robotics",
        "description": "Autonomous space & terrestrial robotics",
        "company_type": "AUTONOMOUS",
        "industry": "ROBOTICS",
        "currency": "USD"
    }
    headers = {"X-Company-ID": "comp-starlight-01", "X-User-ID": "user-founder"}
    response = client.post("/api/v1/companies", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "starlight-robotics"
    assert data["lifecycle"] == "PROPOSED"


def test_company_simulation_route_flow(client: TestClient):
    # 1. Create Snapshot
    headers = {"X-Company-ID": "comp-starlight-01", "X-Environment-ID": "SIMULATION", "X-Simulation-ID": "sim-test-01"}
    snap_res = client.post(
        "/api/v1/simulations/snapshots",
        json={"snapshot_name": "Q3 Baseline", "baseline_metrics": {"revenue_cents": 2000000, "headcount": 5}},
        headers=headers
    )
    assert snap_res.status_code == 201
    snapshot_id = snap_res.json()["snapshot_id"]

    # 2. Create Scenario
    scen_res = client.post(
        "/api/v1/simulations/scenarios",
        json={"name": "2x Staffing Scenario", "variables": {"headcount_multiplier": 2.0, "marketing_boost_pct": 30.0}},
        headers=headers
    )
    assert scen_res.status_code == 201
    scenario_id = scen_res.json()["scenario_id"]

    # 3. Create Simulation Run
    sim_res = client.post(
        "/api/v1/simulations",
        json={"name": "Doubling Staffing Simulation", "scenario_id": scenario_id, "snapshot_id": snapshot_id},
        headers=headers
    )
    assert sim_res.status_code == 201
    simulation_id = sim_res.json()["simulation_id"]

    # 4. Run Scenario Engine
    run_res = client.post(f"/api/v1/simulations/{simulation_id}/run", headers=headers)
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["scenario_name"] == "2x Staffing Scenario"
    assert run_data["simulated_metrics"]["headcount"] == 10

