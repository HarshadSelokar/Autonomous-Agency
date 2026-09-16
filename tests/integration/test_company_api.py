"""Integration tests for Phase 16 Autonomous Company API Endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.database import Base, get_db_session


@pytest.fixture
async def api_client() -> AsyncClient:
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
async def test_company_api_flow(api_client: AsyncClient):
    # 1. Create Company POST /company
    comp_payload = {
        "name": "Acme Autonomous Corp",
        "code": "ACME",
        "mission": "Operate enterprise systems autonomously",
    }
    res = await api_client.post("/company", json=comp_payload)
    assert res.status_code == 201
    comp_data = res.json()
    company_id = comp_data["id"]
    assert comp_data["code"] == "ACME"

    # 2. Get Company GET /company/{company_id}
    res = await api_client.get(f"/company/{company_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Acme Autonomous Corp"

    # 3. Start Cycle POST /company/{company_id}/cycles
    res = await api_client.post(f"/company/{company_id}/cycles", json={"initiated_by_id": "api-user"})
    assert res.status_code == 201
    cycle_data = res.json()
    cycle_id = cycle_data["id"]
    assert cycle_data["state"] == "CREATED"

    # 4. Transition Cycle State POST /company/{company_id}/cycles/{cycle_id}/transition
    res = await api_client.post(
        f"/company/{company_id}/cycles/{cycle_id}/transition",
        json={"target_state": "OBSERVING", "checkpoint_data": {"obs": "done"}},
    )
    assert res.status_code == 200
    assert res.json()["state"] == "OBSERVING"

    # 5. Get Company Health GET /company/{company_id}/health
    res = await api_client.get(f"/company/{company_id}/health")
    assert res.status_code == 200
    health_data = res.json()
    assert health_data["overall_status"] in ["HEALTHY", "BALANCED"]

    # 6. Formulate Strategy POST /company/{company_id}/strategies
    strat_payload = {
        "title": "2026 Q3 Expansion",
        "themes": ["Automation", "Security"],
        "priorities": ["Zero-downtime QA"],
    }
    res = await api_client.post(f"/company/{company_id}/strategies", json=strat_payload)
    assert res.status_code == 200
    assert res.json()["version"] == 1

    # 7. Create Strategy Proposal POST /company/{company_id}/proposals
    prop_payload = {
        "proposal_type": "ORGANIZATIONAL_EVOLUTION",
        "title": "Form Security Department",
        "proposal_body": "Create dedicated security oversight department",
        "reason": "Elevated threat environment",
    }
    res = await api_client.post(f"/company/{company_id}/proposals", json=prop_payload)
    assert res.status_code == 201
    assert res.json()["title"] == "Form Security Department"

    # 8. Run What-If Simulation POST /company/{company_id}/simulations
    sim_payload = {
        "title": "50% Token Price Surge Impact",
        "assumptions": ["Compute price increases 50%"],
        "input_parameters": {"token_price": 0.003},
    }
    res = await api_client.post(f"/company/{company_id}/simulations", json=sim_payload)
    assert res.status_code == 201
    sim_data = res.json()
    assert sim_data["is_authoritative"] is False  # Enforced invariant

    # 9. Get Executive Report GET /company/{company_id}/executive-report
    res = await api_client.get(f"/company/{company_id}/executive-report")
    assert res.status_code == 200
    report_data = res.json()
    assert report_data["company_name"] == "Acme Autonomous Corp"

    # 10. Add Portfolio Item POST /company/{company_id}/portfolio
    port_payload = {
        "title": "AI Company OS Rollout",
        "reference_id": "proj-1",
    }
    res = await api_client.post(f"/company/{company_id}/portfolio", json=port_payload)
    assert res.status_code == 201
    assert res.json()["title"] == "AI Company OS Rollout"
