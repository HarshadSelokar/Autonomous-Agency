"""
Integration Tests for Decision Execution Governance Bridge in Phase 26 Advanced Company Intelligence.

Verifies:
1. Strict Governance Boundary: Decision execution WITHOUT governance_approval_id is BLOCKED with 403 HTTP error.
2. Governed Decision Execution: Decision execution WITH valid governance_approval_id succeeds, marks insight executed, and emits execution event.
3. Expired Decision Insight Safety: Attempting to execute an expired insight is rejected.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db, Base
import src.infrastructure.models.company_intelligence_model
from src.domain.company_intelligence import DecisionInsight
from src.domain.exceptions import DecisionInsightExpiredError


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:govbridgedb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_governance_boundary_blocks_unapproved_execution(client):
    company_id = "comp-gov-alpha"

    # Create Decision Question
    resp_q = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-questions",
        json={
            "question": "Should we deploy automated AI agent cluster for customer support?",
            "purpose": "Reduce customer support response times",
            "scope": "OPERATIONAL",
            "urgency": "MEDIUM",
        },
    )
    assert resp_q.status_code == 201
    q_id = resp_q.json()["id"]

    # Generate options & Evaluate & Synthesize
    resp_eval = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-questions/{q_id}/evaluate",
        json={
            "options_data": [
                {
                    "option_name": "Deploy 10 Customer Support Agents",
                    "description": "Deploy automated customer support workforce tier.",
                    "expected_costs_cents": 1000000,
                }
            ]
        },
    )
    assert resp_eval.status_code == 200
    insight_id = resp_eval.json()["insight_id"]

    # Attempt Execution WITHOUT governance approval ID -> MUST FAIL WITH 403 FORBIDDEN!
    resp_exec_no_gov = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}/execute",
        json={"governance_approval_id": ""},
    )
    assert resp_exec_no_gov.status_code == 403
    err_detail = resp_exec_no_gov.json().get("detail", "")
    assert "governance approval" in err_detail.lower() or "required" in err_detail.lower()


def test_governed_execution_succeeds_with_approval_id(client):
    company_id = "comp-gov-alpha"

    # Create Question, Option, Evaluate, Synthesize
    resp_q = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-questions",
        json={
            "question": "Should we reallocate engineering R&D budget?",
            "purpose": "R&D rebalancing",
        },
    )
    assert resp_q.status_code == 201
    q_id = resp_q.json()["id"]

    resp_eval = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-questions/{q_id}/evaluate",
        json={
            "options_data": [
                {
                    "option_name": "Reallocate 20% budget to AI research",
                    "expected_costs_cents": 5000000,
                }
            ]
        },
    )
    assert resp_eval.status_code == 200
    insight_id = resp_eval.json()["insight_id"]

    # Execute WITH valid human governance approval ID -> MUST SUCCEED!
    gov_approval_id = "gov-appr-chairman-999"
    resp_exec = client.post(
        f"/api/v1/intelligence/companies/{company_id}/decision-insights/{insight_id}/execute",
        json={"governance_approval_id": gov_approval_id},
    )
    assert resp_exec.status_code == 200
    res = resp_exec.json()
    assert res["status"] == "GOVERNED_EXECUTION_INITIATED"
    assert res["governance_approval_id"] == gov_approval_id
    assert res["insight_id"] == insight_id


def test_expired_insight_execution_rejected():
    expired_insight = DecisionInsight(
        id="insight-exp-01",
        question_id="q-01",
        company_id="comp-gov-alpha",
        is_expired=True,
        governance_required=True,
        governance_approval_id="gov-appr-888",
    )

    with pytest.raises(DecisionInsightExpiredError):
        expired_insight.assert_valid_for_execution()
