"""
Unit & REST API Route Tests for Phase 26 Company Intelligence & Decision Support Endpoints.
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
    engine = create_async_engine("sqlite+aiosqlite:///file:inteltestdb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_company_intelligence_routes_full_flow(client: TestClient):
    company_id = "comp-api-test-01"

    # 1. Start Intelligence Run
    run_res = client.post(f"/api/v1/intelligence/companies/{company_id}/runs", json={"purpose": "Quarterly Performance Audit"})
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["findings_count"] == 2

    # 2. Get Company Health & Bottlenecks
    health_res = client.get(f"/api/v1/intelligence/companies/{company_id}/health")
    assert health_res.status_code == 200
    assert health_res.json()["overall_health_status"] == "BALANCED"

    bn_res = client.get(f"/api/v1/intelligence/companies/{company_id}/bottlenecks")
    assert bn_res.status_code == 200
    assert len(bn_res.json()) > 0

    # 3. Create Decision Question
    q_res = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-questions",
        json={"question": "Should engineering capacity be expanded?", "purpose": "Clear release backlog", "urgency": "HIGH"},
    )
    assert q_res.status_code == 201
    question_id = q_res.json()["id"]

    # 4. Evaluate Options & Synthesize Insight
    eval_res = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-questions/{question_id}/evaluate",
        json={
            "options_data": [
                {
                    "option_name": "Option 1: Add 5 Engineers",
                    "description": "Expand capacity by 25%",
                    "expected_costs_cents": 5000000,
                }
            ]
        },
    )
    assert eval_res.status_code == 200
    insight_id = eval_res.json()["insight_id"]

    # 5. Fetch Decision Insight
    insight_res = client.get(f"/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}")
    assert insight_res.status_code == 200
    assert insight_res.json()["governance_required"] is True

    # 6. Attempt execution without approval -> 403 Forbidden
    exec_fail = client.post(f"/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}/execute", json={"governance_approval_id": ""})
    assert exec_fail.status_code == 403

    # 7. Execute with governance approval -> 200 OK
    exec_pass = client.post(f"/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}/execute", json={"governance_approval_id": "gov-appr-777"})
    assert exec_pass.status_code == 200
    assert exec_pass.json()["status"] == "GOVERNED_EXECUTION_INITIATED"

    # 8. Post-Execution Decision Outcome Evaluation
    outcome_res = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-outcomes/evaluate",
        json={
            "insight_id": insight_id,
            "executed_option_id": eval_res.json()["recommended_option_id"],
            "expected_outcomes": {"revenue_cents": 10000000},
            "actual_outcomes": {"revenue_cents": 10800000},
        },
    )
    assert outcome_res.status_code == 201
    assert outcome_res.json()["variance_analysis"]["revenue_variance_pct"] == 8.0
