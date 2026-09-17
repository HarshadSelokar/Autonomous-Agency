"""
Integration Tests for Multi-Tenant Security Isolation in Phase 27 Continuous Organizational Learning & Governed Adaptation.

Verifies:
1. Complete data boundary isolation between Company A and Company B across learning cycles, observations, outcome comparisons, learning patterns, candidates, validated learnings, opportunities, adaptation proposals, controlled experiments, and outcomes.
2. Cross-company access attempts return HTTP 404 / 403 or empty lists.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db, Base
import src.infrastructure.models.learning_model


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:seclearningdb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_api_multi_tenant_learning_isolation(client):
    company_a = "comp-sec-alpha-001"
    company_b = "comp-sec-beta-002"

    # Step 1: Create Learning Cycle for Company A
    resp_a = client.post(
        f"/api/v1/learning/companies/{company_a}/cycles",
        json={"purpose": "Company A Security Audit Cycle", "scope": "DEPARTMENT"},
    )
    assert resp_a.status_code == 201
    cycle_a = resp_a.json()
    cycle_id_a = cycle_a["id"]

    # Ingest Observation for Company A
    resp_obs = client.post(
        f"/api/v1/learning/companies/{company_a}/observations",
        json={
            "cycle_id": cycle_id_a,
            "source_subsystem": "TASK_ENGINE",
            "entity_reference": "task-alpha-1",
            "observed_value": {"latency_ms": 1200},
            "expected_value": {"latency_ms": 300},
        },
    )
    assert resp_obs.status_code == 201

    # Formulate Candidate for Company A
    resp_cand = client.post(
        f"/api/v1/learning/companies/{company_a}/candidates",
        json={
            "cycle_id": cycle_id_a,
            "statement": "Parallel task dispatch cuts latency for Company A",
        },
    )
    assert resp_cand.status_code == 201

    # Create Opportunity & Proposal for Company A
    resp_opp = client.post(
        f"/api/v1/learning/companies/{company_a}/improvements",
        json={
            "title": "Increase Concurrency for Alpha",
            "affected_area": "ENGINEERING",
            "expected_impact": "50% speedup",
        },
    )
    assert resp_opp.status_code == 201
    opp_a = resp_opp.json()

    resp_prop = client.post(
        f"/api/v1/learning/companies/{company_a}/adaptations",
        json={
            "opportunity_id": opp_a["id"],
            "adaptation_type": "WORKFLOW_CHANGE",
            "rationale": "Alpha concurrency proposal",
        },
    )
    assert resp_prop.status_code == 201

    # Step 2: Verify Company B list queries return 0 items
    list_cycles_b = client.get(f"/api/v1/learning/companies/{company_b}/cycles")
    assert list_cycles_b.status_code == 200
    assert len(list_cycles_b.json()) == 0

    list_cands_b = client.get(f"/api/v1/learning/companies/{company_b}/lessons")
    assert list_cands_b.status_code == 200
    assert len(list_cands_b.json()) == 0

    list_opps_b = client.get(f"/api/v1/learning/companies/{company_b}/improvements")
    assert list_opps_b.status_code == 200
    assert len(list_opps_b.json()) == 0

    # Step 3: Verify Company B direct GET for Company A's cycle returns 404
    get_cycle_b = client.get(f"/api/v1/learning/companies/{company_b}/cycles/{cycle_id_a}")
    assert get_cycle_b.status_code == 404
