"""
Unit & API route tests for Phase 23 Business Operations REST endpoints.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.infrastructure.database import get_db
from src.infrastructure.database import Base
import src.infrastructure.models.business_model


@pytest.fixture
def client():
    engine = create_async_engine("sqlite+aiosqlite:///file:biztestdb?mode=memory&cache=shared&uri=true", echo=False)

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


def test_business_api_endpoints_flow(client: TestClient):
    # 1. Create Business Account
    acc_res = client.post(
        "/business/accounts",
        json={
            "account_code": "1000",
            "name": "Primary Operating",
            "account_type": "OPERATING",
            "initial_balance_cents": 1000000,
        },
    )
    assert acc_res.status_code == 201
    acc_id = acc_res.json()["id"]

    # List accounts
    accs_list = client.get("/business/accounts")
    assert accs_list.status_code == 200
    assert len(accs_list.json()) >= 1

    # 2. Record Revenue
    rev_res = client.post(
        "/business/revenue",
        json={
            "source": "Stripe Payments",
            "customer_id": "cust-api-1",
            "product_service": "Platform Subscription",
            "amount_cents": 500000,
        },
    )
    assert rev_res.status_code == 201

    # 3. Create Draft Invoice
    inv_res = client.post(
        "/business/invoices",
        json={
            "customer_id": "cust-api-1",
            "lines": [{"description": "Custom Development", "quantity": 1, "unit_price_cents": 200000}],
        },
    )
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Issue Invoice
    issue_res = client.post(
        f"/business/invoices/{inv_id}/issue",
        json={"actor_id": "mgr-api", "governance_approval_id": "gov-app-555"},
    )
    assert issue_res.status_code == 200
    assert issue_res.json()["status"] == "SENT"

    # 4. Procurement Flow
    proc_res = client.post(
        "/business/procurement",
        json={
            "requester_id": "emp-dev-1",
            "item_description": "Cloud GPU Instance",
            "estimated_cents": 150000,
        },
    )
    assert proc_res.status_code == 201
    proc_id = proc_res.json()["id"]

    app_res = client.post(
        f"/business/procurement/{proc_id}/approve",
        json={
            "approver_id": "mgr-api",
            "vendor_id": "vendor-aws",
            "governance_approval_id": "gov-app-556",
        },
    )
    assert app_res.status_code == 200
    assert "po_number" in app_res.json()

    # 5. Reconciliation Endpoint
    recon_res = client.post(
        "/business/reconciliation",
        json={
            "external_statements": [{"external_ref": "ext-1", "amount_cents": 500000, "currency": "USD"}],
            "source_provider": "STRIPE",
        },
    )
    assert recon_res.status_code == 200

    # 6. Cash Flow Endpoint
    cf_res = client.get("/business/cash-flow")
    assert cf_res.status_code == 200
    assert "actual_inflow_cents" in cf_res.json()
