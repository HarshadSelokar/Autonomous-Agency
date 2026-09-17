"""
Unit & REST API Route Tests for Phase 27 Continuous Organizational Learning & Adaptation Endpoints.
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
    engine = create_async_engine("sqlite+aiosqlite:///file:learningroutetestdb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_learning_routes_full_flow(client: TestClient):
    company_id = "comp-api-test-learning"

    # 1. Start Learning Cycle
    cycle_res = client.post(
        f"/api/v1/learning/companies/{company_id}/cycles",
        json={"purpose": "Operational Efficiency Audit", "scope": "COMPANY"},
    )
    assert cycle_res.status_code == 201
    cycle_id = cycle_res.json()["id"]

    # 2. Ingest Observation
    obs_res = client.post(
        f"/api/v1/learning/companies/{company_id}/observations",
        json={
            "cycle_id": cycle_id,
            "source_subsystem": "TASK_ENGINE",
            "entity_reference": "task-555",
            "observed_value": {"duration_sec": 900},
            "expected_value": {"duration_sec": 300},
        },
    )
    assert obs_res.status_code == 201

    # 3. Compare Expected vs Actual
    comp_res = client.post(
        f"/api/v1/learning/companies/{company_id}/comparisons",
        json={
            "cycle_id": cycle_id,
            "domain": "TASK_DURATION",
            "metric_name": "duration_sec",
            "expected_value": 300.0,
            "actual_value": 900.0,
        },
    )
    assert comp_res.status_code == 201
    assert comp_res.json()["variance"] == 600.0

    # 4. Generate Candidate Lesson
    cand_res = client.post(
        f"/api/v1/learning/companies/{company_id}/candidates",
        json={
            "cycle_id": cycle_id,
            "statement": "Complex DB migrations cause sprint delivery delays.",
        },
    )
    assert cand_res.status_code == 201
    cand_id = cand_res.json()["id"]

    # 5. Validate Candidate
    val_res = client.post(
        f"/api/v1/learning/companies/{company_id}/candidates/{cand_id}/validate",
        json={"validation_method": "HISTORICAL_ANALYSIS", "is_valid": True, "evidence_score": 0.90},
    )
    assert val_res.status_code == 200

    # 6. Fetch Validated Lessons
    lessons_res = client.get(f"/api/v1/learning/companies/{company_id}/lessons")
    assert lessons_res.status_code == 200
    assert len(lessons_res.json()) == 1

    # 7. Create Improvement Opportunity
    opp_res = client.post(
        f"/api/v1/learning/companies/{company_id}/improvements",
        json={
            "title": "Automate Pre-flight Migration Checks",
            "affected_area": "ENGINEERING",
            "expected_impact": "Prevents migration blockages",
        },
    )
    assert opp_res.status_code == 201
    opp_id = opp_res.json()["id"]

    # 8. Propose Adaptation
    prop_res = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations",
        json={
            "opportunity_id": opp_id,
            "adaptation_type": "VERIFICATION_RULE_CHANGE",
            "risk_level": "MEDIUM",
            "rationale": "Add automated schema dry-run rule.",
        },
    )
    assert prop_res.status_code == 201
    adaptation_id = prop_res.json()["id"]

    # 9. Attempt experiment without governance -> 403 Forbidden
    exp_fail = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{adaptation_id}/experiment",
        json={"governance_approval_id": ""},
    )
    assert exp_fail.status_code == 403

    # 10. Execute experiment WITH governance approval -> 200 OK
    exp_pass = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{adaptation_id}/experiment",
        json={"governance_approval_id": "gov-appr-888-learning"},
    )
    assert exp_pass.status_code == 200
    exec_id = exp_pass.json()["execution_id"]

    # 11. Evaluate Experiment Outcome
    out_res = client.post(
        f"/api/v1/learning/companies/{company_id}/adaptations/{adaptation_id}/evaluate-outcome",
        json={
            "execution_id": exec_id,
            "expected_metrics": {"duration_sec": 300},
            "actual_metrics": {"duration_sec": 280},
        },
    )
    assert out_res.status_code == 200
    assert out_res.json()["has_regression"] is False

    # 12. Adopt Adaptation
    adopt_res = client.post(f"/api/v1/learning/companies/{company_id}/adaptations/{adaptation_id}/adopt")
    assert adopt_res.status_code == 200
    assert adopt_res.json()["status"] == "ADOPTED"

    # 13. Fetch Learning Context
    ctx_res = client.get(f"/api/v1/learning/companies/{company_id}/context")
    assert ctx_res.status_code == 200
    assert "ORGANIZATIONAL LEARNING CONTEXT" in ctx_res.json()["learning_context"]
