"""
Integration Tests for Governed Venture Bridge & Governance Safety Boundary in Phase 28.

Verifies:
1. Strict Governance Boundary: Venture proposals cannot initialize or create companies without a valid `governance_approval_id`.
2. Direct initialization without approval ID returns HTTP 403 (UnauthorizedVentureCreationError).
3. Attaching valid `governance_approval_id` permits initialization.
4. Launch attempt without launch readiness returns HTTP 400 (VentureLaunchBlockedError).
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
    engine = create_async_engine("sqlite+aiosqlite:///file:govventuredb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_venture_governance_boundary_enforcement(client):
    company_id = "comp-gov-venture-001"

    # Step 1: Create Opportunity, Business Case, and Proposal
    resp_opp = client.post(
        f"/api/v1/ventures/companies/{company_id}/opportunities",
        json={
            "title": "Autonomous Medical Diagnostics AI",
            "description": "Medical imaging diagnostics venture.",
            "problem_statement": "Diagnostic delay.",
            "customer_need": "Automated CT scan reading.",
        },
    )
    assert resp_opp.status_code == 201
    opp = resp_opp.json()

    resp_bcase = client.post(
        f"/api/v1/ventures/companies/{company_id}/business-cases",
        json={
            "opportunity_id": opp["id"],
            "title": "Medical AI Business Case",
            "expected_roi": 0.50,
        },
    )
    assert resp_bcase.status_code == 201
    bcase = resp_bcase.json()

    resp_prop = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals",
        json={
            "opportunity_id": opp["id"],
            "business_case_id": bcase["id"],
            "title": "MediPulse AI Inc.",
            "venture_type": "NEW_COMPANY",
        },
    )
    assert resp_prop.status_code == 201
    proposal = resp_prop.json()
    proposal_id = proposal["id"]

    # Step 2: Attempt Initialization WITHOUT Governance Approval -> MUST FAIL HTTP 403
    resp_init_fail = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/initialize",
        json={"target_structure": "NEW_COMPANY"},
    )
    assert resp_init_fail.status_code == 403
    assert "Unauthorized venture creation" in resp_init_fail.json()["detail"]

    # Step 3: Attach Governance Approval ID
    resp_gov = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/approve",
        json={"governance_approval_id": "gov-appr-med-pass-900"},
    )
    assert resp_gov.status_code == 200
    assert resp_gov.json()["governance_approval_id"] == "gov-appr-med-pass-900"

    # Step 4: Initialize Venture WITH Governance Approval ID -> MUST SUCCEED
    resp_init_pass = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/initialize",
        json={"target_structure": "NEW_COMPANY"},
    )
    assert resp_init_pass.status_code == 200
    assert resp_init_pass.json()["governance_approval_id"] == "gov-appr-med-pass-900"

    # Step 5: Attempt Launch WITHOUT Readiness Assessment -> MUST FAIL HTTP 400
    resp_launch_fail = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/launch"
    )
    assert resp_launch_fail.status_code == 400
    assert "Venture launch blocked" in resp_launch_fail.json()["detail"]

    # Step 6: Assess Launch Readiness & Launch -> MUST SUCCEED
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

    resp_launch_pass = client.post(
        f"/api/v1/ventures/companies/{company_id}/proposals/{proposal_id}/launch"
    )
    assert resp_launch_pass.status_code == 200
    assert resp_launch_pass.json()["status"] == "LAUNCHED"
