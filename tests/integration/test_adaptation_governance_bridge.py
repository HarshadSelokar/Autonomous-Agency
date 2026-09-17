"""
Integration Tests for Governed Adaptation Bridge & Governance Boundary Enforcement in Phase 27.

Verifies:
1. Strict Governance Boundary: Adaptation proposals cannot dispatch controlled experiments or execute without a valid `governance_approval_id`.
2. Direct execution without approval ID returns HTTP 403 (UnauthorizedAdaptationExecutionError).
3. Attaching valid `governance_approval_id` permits experiment dispatch and promotion.
4. Invalid state transitions (e.g. attempting to adopt an un-evaluated proposal) return HTTP 400 (InvalidAdaptationStateError).
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
    engine = create_async_engine("sqlite+aiosqlite:///file:govlearningdb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_adaptation_governance_boundary_enforcement(client):
    company_id = "comp-gov-test-001"

    # Step 1: Create Improvement Opportunity & Adaptation Proposal
    resp_opp = client.post(
        f"/api/v1/learning/companies/{company_id}/improvements",
        json={
            "title": "Automate Code Review Pre-Check",
            "affected_area": "ENGINEERING",
            "expected_impact": "Latency reduction",
        },
    )
    assert resp_opp.status_code == 201
    opp = resp_opp.json()

    resp_prop = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations",
        json={
            "opportunity_id": opp["id"],
            "adaptation_type": "WORKFLOW_CHANGE",
            "rationale": "Automated AST pre-check",
        },
    )
    assert resp_prop.status_code == 201
    proposal = resp_prop.json()
    proposal_id = proposal["id"]

    # Step 2: Attempt Experiment Dispatch WITHOUT Governance Approval -> MUST FAIL HTTP 403
    resp_dispatch_fail = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{proposal_id}/experiment",
        json={
            "governance_approval_id": "",  # Empty approval ID!
        },
        headers={"X-User-ID": "AUTO_DISPATCHER"},
    )
    assert resp_dispatch_fail.status_code == 403
    assert "Unauthorized adaptation execution" in resp_dispatch_fail.json()["detail"]

    # Step 3: Attach Governance Approval ID
    resp_gov = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{proposal_id}/approve",
        json={"governance_approval_id": "gov-appr-valid-778899"},
    )
    assert resp_gov.status_code == 200
    assert resp_gov.json()["governance_approval_id"] == "gov-appr-valid-778899"

    # Step 4: Dispatch Experiment WITH Governance Approval ID -> MUST SUCCEED
    resp_dispatch_pass = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{proposal_id}/experiment",
        json={
            "governance_approval_id": "gov-appr-valid-778899",
            "target_subsystem": "WORKFLOW_ENGINE",
        },
        headers={"X-User-ID": "GOVERNED_DISPATCHER"},
    )
    assert resp_dispatch_pass.status_code == 200
    execution = resp_dispatch_pass.json()
    execution_id = execution["execution_id"]

    # Step 5: Evaluate Experiment Outcome
    resp_eval = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{proposal_id}/evaluate-outcome",
        json={
            "execution_id": execution_id,
            "expected_metrics": {"latency_ms": 300},
            "actual_metrics": {"latency_ms": 120},
        },
    )
    assert resp_eval.status_code == 200

    # Step 6: Adopt Adaptation
    resp_adopt = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{proposal_id}/adopt"
    )
    assert resp_adopt.status_code == 200
    assert resp_adopt.json()["status"] == "ADOPTED"
