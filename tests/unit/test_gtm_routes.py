"""
Unit & API route tests for Phase 24 Product, Customer & GTM REST endpoints.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db
from src.infrastructure.database import Base
import src.infrastructure.models.gtm_model
import src.infrastructure.models.business_model


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:gtmtestdb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_gtm_api_routes_flow(client: TestClient):
    # 1. Create Product
    prod_res = client.post(
        "/gtm/products",
        json={
            "name": "Autonomous AI Agent OS",
            "code": "PROD-AIOS-01",
            "description": "Enterprise multi-agent autonomous organization system",
            "owner_employee_id": "emp-cto-1",
            "base_price_cents": 10000000,
        },
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 2. Record Product Feedback
    fb_res = client.post(
        f"/gtm/products/{prod_id}/feedback",
        json={
            "customer_id": "cust-beta-1",
            "summary": "Need automated GTM analytics",
            "raw_content": "We need full funnel visibility from lead to opportunity to revenue.",
            "category": "FEATURE_REQUEST",
            "importance_score": 5,
        },
    )
    assert fb_res.status_code == 201

    # 3. Create Lead & Qualify
    lead_res = client.post(
        "/gtm/leads",
        json={
            "company_name": "Titan Technologies",
            "contact_name": "Mark Vance",
            "contact_email": "mark@titan.com",
            "source": "INBOUND_WEB",
        },
    )
    assert lead_res.status_code == 201
    lead_id = lead_res.json()["id"]

    qual_res = client.post(f"/gtm/leads/{lead_id}/qualify", json={"qualified_by": "sales-rep-1", "score": 90})
    assert qual_res.status_code == 200
    assert qual_res.json()["status"] == "QUALIFIED"

    # 4. Create Opportunity
    opp_res = client.post(
        "/gtm/opportunities",
        json={
            "title": "Titan Enterprise Deal",
            "product_id": prod_id,
            "owner_id": "sales-rep-1",
            "estimated_value_cents": 10000000,
            "lead_id": lead_id,
        },
    )
    assert opp_res.status_code == 201
    opp_id = opp_res.json()["id"]

    # 5. Create Proposal & Approve
    prop_res = client.post(
        "/gtm/proposals",
        json={
            "opportunity_id": opp_id,
            "title": "Titan AI OS Proposal",
            "product_id": prod_id,
            "base_amount_cents": 10000000,
            "owner_id": "sales-rep-1",
            "discount_pct": 10.0,
        },
    )
    assert prop_res.status_code == 201
    prop_id = prop_res.json()["id"]

    app_res = client.post(f"/gtm/proposals/{prop_id}/approve", json={"actor_id": "sales-rep-1"})
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "SENT"

    # 6. Deal Won Execution (Triggers Phase 23 Order -> Invoice -> Payment -> Onboarding)
    won_res = client.post(f"/gtm/opportunities/{opp_id}/won", json={"actor_id": "sales-rep-1", "governance_approval_id": "gov-app-won-999"})
    assert won_res.status_code == 200
    assert won_res.json()["status"] == "WON_AND_ONBOARDING_INITIATED"

    # 7. Support Case
    case_res = client.post(
        "/gtm/support",
        json={
            "customer_id": won_res.json()["customer_id"],
            "subject": "Initial Setup Query",
            "description": "How do we configure multi-agent swarms?",
            "priority": "MEDIUM",
        },
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    res_res = client.post(f"/gtm/support/{case_id}/resolve", json={"resolved_by": "supp-agent-1", "resolution_notes": "Provided onboarding doc link."})
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
