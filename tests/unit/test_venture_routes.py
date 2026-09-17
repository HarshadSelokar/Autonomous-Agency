"""
Unit Tests for Phase 28 Venture REST API Endpoints.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db, Base
import src.infrastructure.models.venture_model


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:venturedb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_venture_routes_full_pipeline(client):
    company_id = "comp-route-test-01"

    # Step 1: Discover Opportunity
    resp_opp = client.post(
        f"/api/v1/ventures/companies/{company_id}/opportunities",
        json={
            "title": "Autonomous Supply Chain AI Venture",
            "description": "Enterprise AI for real-time logistics.",
            "problem_statement": "Delayed container shipments.",
            "customer_need": "Real-time port tracking.",
        },
    )
    assert resp_opp.status_code == 201
    opp = resp_opp.json()
    opp_id = opp["id"]

    # Step 2: Validate Opportunity
    resp_val = client.post(
        f"/api/v1/ventures/companies/{company_id}/opportunities/{opp_id}/validate",
        json={
            "validation_method": "PORT_TELEMETRY_DATA_ANALYSIS",
            "evidence_summary": "Analyzed 5,000 port shipping records.",
            "confidence_score": 0.92,
        },
    )
    assert resp_val.status_code == 200

    # Step 3: Construct Business Case
    resp_bcase = client.post(
        f"/api/v1/ventures/companies/{company_id}/business-cases",
        json={
            "opportunity_id": opp_id,
            "title": "Supply Chain AI Business Case",
            "expected_roi": 0.42,
        },
    )
    assert resp_bcase.status_code == 201
    bcase_id = resp_bcase.json()["id"]

    # Step 4: Propose Venture
    resp_prop = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals",
        json={
            "opportunity_id": opp_id,
            "business_case_id": bcase_id,
            "title": "PortPulse AI Inc.",
            "venture_type": "NEW_COMPANY",
            "required_budget_usd": 20000000,
        },
    )
    assert resp_prop.status_code == 201
    proposal_id = resp_prop.json()["id"]

    # Step 5: Attempt Initialization WITHOUT Governance Approval -> MUST FAIL 403
    resp_init_fail = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/initialize",
        json={"target_structure": "NEW_COMPANY"},
    )
    assert resp_init_fail.status_code == 403

    # Step 6: Attach Governance Approval
    resp_gov = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/approve",
        json={"governance_approval_id": "gov-appr-venture-9001"},
    )
    assert resp_gov.status_code == 200

    # Step 7: Initialize Venture WITH Governance Approval -> MUST SUCCEED
    resp_init_pass = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/initialize",
        json={"target_structure": "NEW_COMPANY"},
    )
    assert resp_init_pass.status_code == 200
    assert resp_init_pass.json()["governance_approval_id"] == "gov-appr-venture-9001"

    # Step 8: Assess Launch Readiness & Launch
    resp_readiness = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/launch-readiness",
        json={
            "product_ready": True,
            "technical_ready": True,
            "security_ready": True,
            "financial_ready": True,
            "governance_ready": True,
        },
    )
    assert resp_readiness.status_code == 200
    assert resp_readiness.json()["status"] == "READY"

    resp_launch = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/launch"
    )
    assert resp_launch.status_code == 200
    assert resp_launch.json()["status"] == "LAUNCHED"

    # Step 9: Get Portfolio
    resp_port = client.get(f"/api/v1/ventures/companies/{company_id}/portfolio")
    assert resp_port.status_code == 200
    assert resp_port.json()["opportunities_count"] == 1
