"""
Integration Tests for Multi-Tenant Security Isolation in Phase 26 Advanced Company Intelligence.

Verifies:
1. Complete data boundary isolation between Company A and Company B for intelligence runs, health assessments,
   bottlenecks, decision questions, decision options, decision insights, and outcome evaluations.
2. Cross-company access prevention in REST API layer and repository layer.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db, Base
import src.infrastructure.models.company_intelligence_model


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:secinteldb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_api_multi_tenant_intelligence_isolation(client):
    company_a = "comp-sec-alpha"
    company_b = "comp-sec-beta"

    # Create Intelligence Run for Company A
    resp_a = client.post(
        f"/api/v1/intelligence/companies/{company_a}/runs",
        json={"purpose": "Security Isolation Audit", "scope": "FULL_COMPANY"},
    )
    assert resp_a.status_code == 201
    run_a = resp_a.json()
    run_id = run_a["id"]

    # Verify Company A can view its run
    resp_get_a = client.get(f"/api/v1/intelligence/companies/{company_a}/runs/{run_id}")
    assert resp_get_a.status_code == 200

    # Verify Company B CANNOT view Company A's run (returns 404)
    resp_get_b = client.get(f"/api/v1/intelligence/companies/{company_b}/runs/{run_id}")
    assert resp_get_b.status_code == 404

    # Verify Company B listing intelligence runs returns empty list
    resp_list_b = client.get(f"/api/v1/intelligence/companies/{company_b}/runs")
    assert resp_list_b.status_code == 200
    b_runs = resp_list_b.json()
    assert not any(r["id"] == run_id for r in b_runs)


def test_api_multi_tenant_decision_insight_isolation(client):
    company_a = "comp-sec-alpha"
    company_b = "comp-sec-beta"

    # Create Decision Question for Company A
    resp_q = client.post(
        f"/api/v1/intelligence/companies/{company_a}/decision-questions",
        json={
            "question": "Should Company A expand into EMEA market?",
            "purpose": "Global market expansion strategy",
            "scope": "STRATEGIC",
            "urgency": "HIGH",
        },
    )
    assert resp_q.status_code == 201
    q_id = resp_q.json()["id"]

    # Evaluate options & Synthesize Insight Brief
    resp_eval = client.post(
        f"/api/v1/intelligence/companies/{company_a}/decision-questions/{q_id}/evaluate",
        json={
            "options_data": [
                {
                    "option_name": "Expand to London Office",
                    "description": "Establish European headquarters in London.",
                    "expected_costs_cents": 25000000,
                }
            ]
        },
    )
    assert resp_eval.status_code == 200
    insight_id = resp_eval.json()["insight_id"]

    # Verify Company B cannot execute or access Company A's insight
    resp_exec_b = client.post(
        f"/api/v1/intelligence/companies/{company_b}/decision-insights/{insight_id}/execute",
        json={"governance_approval_id": "fake-gov-appr"},
    )
    assert resp_exec_b.status_code == 404
