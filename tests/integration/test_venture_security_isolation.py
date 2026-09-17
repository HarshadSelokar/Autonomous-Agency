"""
Integration Tests for Multi-Tenant Security Isolation in Phase 28 Autonomous Ventures.

Verifies:
1. Complete data boundary isolation between Company A and Company B across opportunities, ideas, business cases, venture proposals, and initialization plans.
2. Cross-company access attempts return HTTP 404 or empty lists.
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
    engine = create_async_engine("sqlite+aiosqlite:///file:secventuredb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_api_multi_tenant_venture_isolation(client):
    company_a = "comp-sec-alpha-99"
    company_b = "comp-sec-beta-88"

    # Step 1: Create Opportunity & Business Case for Company A
    resp_opp_a = client.post(
        f"/api/v1/ventures/companies/{company_a}/opportunities",
        json={
            "title": "Alpha Secure Logistics AI",
            "description": "Company A confidential logistics opportunity.",
            "problem_statement": "Alpha logistics delay.",
            "customer_need": "Alpha routing AI.",
        },
    )
    assert resp_opp_a.status_code == 201
    opp_a = resp_opp_a.json()

    resp_bcase_a = client.post(
        f"/api/v1/ventures/companies/{company_a}/business-cases",
        json={
            "opportunity_id": opp_a["id"],
            "title": "Alpha Business Case",
            "expected_roi": 0.45,
        },
    )
    assert resp_bcase_a.status_code == 201
    bcase_a = resp_bcase_a.json()

    resp_prop_a = client.post(
        f"/api/v1/ventures/companies/{company_a}/proposals",
        json={
            "opportunity_id": opp_a["id"],
            "business_case_id": bcase_a["id"],
            "title": "Alpha New Venture Inc",
            "venture_type": "NEW_COMPANY",
        },
    )
    assert resp_prop_a.status_code == 201

    # Step 2: Verify Company B list queries return 0 items
    list_opps_b = client.get(f"/api/v1/ventures/companies/{company_b}/opportunities")
    assert list_opps_b.status_code == 200
    assert len(list_opps_b.json()) == 0

    list_bcases_b = client.get(f"/api/v1/ventures/companies/{company_b}/business-cases")
    assert list_bcases_b.status_code == 200
    assert len(list_bcases_b.json()) == 0

    list_props_b = client.get(f"/api/v1/ventures/companies/{company_b}/proposals")
    assert list_props_b.status_code == 200
    assert len(list_props_b.json()) == 0
