"""Integration tests for Phase 18 Institutional Knowledge & Experiments API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.infrastructure.database import Base, get_db, get_db_session


@pytest.fixture
async def api_client() -> AsyncClient:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_knowledge_api_workflow(api_client: AsyncClient):
    # 1. Create Knowledge Item Candidate
    item_payload = {
        "statement": "Database connection pooling reduces latency by 35%",
        "knowledge_type": "FACT",
        "scope": "COMPANY",
        "confidence": 0.85,
        "source_type": "BENCHMARK_TEST",
        "task_id": "task-bench-101",
        "tags": ["database", "performance"],
    }
    resp1 = await api_client.post("/knowledge", json=item_payload)
    assert resp1.status_code == 201
    data1 = resp1.json()
    item_id = data1["id"]
    assert data1["status"] == "CANDIDATE"
    assert data1["authority"] == "UNVERIFIED"

    # 2. Get Knowledge Item
    resp2 = await api_client.get(f"/knowledge/{item_id}")
    assert resp2.status_code == 200
    assert resp2.json()["statement"] == item_payload["statement"]

    # 3. Validate Knowledge Item (Independent Evidence Check)
    val_payload = {
        "validator_id": "system-val-1",
        "evidence_ids": ["ev_benchmark_logs_555"],
        "rationale": "Empirical log verification completed",
    }
    resp3 = await api_client.post(f"/knowledge/{item_id}/validate", json=val_payload)
    assert resp3.status_code == 200
    assert resp3.json()["validation_status"] == "PASSED"

    # Verify updated item authority
    resp2_updated = await api_client.get(f"/knowledge/{item_id}")
    assert resp2_updated.json()["authority"] == "VALIDATED"


@pytest.mark.asyncio
async def test_procedure_api_workflow(api_client: AsyncClient):
    # 1. Create Procedure
    proc_payload = {
        "title": "PostgreSQL Failover Procedure",
        "purpose": "Standard step-by-step failover process",
        "steps": [
            {"step": 1, "action": "Promote read replica"},
            {"step": 2, "action": "Update DNS endpoint"},
        ],
        "expected_outcome": "Database operational",
        "scope": "COMPANY",
    }
    resp1 = await api_client.post("/knowledge/procedures", json=proc_payload)
    assert resp1.status_code == 201
    proc_id = resp1.json()["id"]
    assert resp1.json()["is_governance_approved"] is False

    # 2. Approve Procedure with Governance
    resp2 = await api_client.post(
        f"/knowledge/procedures/{proc_id}/approve",
        params={"governance_approval_id": "gov-appr-999"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["is_governance_approved"] is True
    assert resp2.json()["validation_status"] == "AUTHORITATIVE"


@pytest.mark.asyncio
async def test_experiment_api_workflow(api_client: AsyncClient):
    # 1. Propose HIGH risk experiment
    exp_payload = {
        "title": "Autonomous Query Optimization Experiment",
        "hypothesis": "Dynamic indexing reduces query execution time by 40%",
        "risk_level": "HIGH",
        "treatment_params": {"max_index_limit": 5},
    }
    resp1 = await api_client.post("/experiments", json=exp_payload)
    assert resp1.status_code == 201
    exp_data = resp1.json()
    exp_id = exp_data["id"]
    assert exp_data["status"] == "PROPOSED"
    assert exp_data["is_isolated"] is True  # Invariant check!

    # 2. Start HIGH risk experiment without governance approval -> 400 Bad Request
    resp2_fail = await api_client.post(f"/experiments/{exp_id}/start")
    assert resp2_fail.status_code == 400

    # 3. Start HIGH risk experiment with governance approval -> 200 OK
    resp2 = await api_client.post(
        f"/experiments/{exp_id}/start",
        json={"governance_approval_id": "gov-exp-approval-101"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ACTIVE"

    # 4. Complete experiment
    comp_payload = {
        "results": {"latency_reduction_pct": 42.5},
        "conclusion": "Query latency reduced by 42.5%, index limit optimal.",
    }
    resp3 = await api_client.post(f"/experiments/{exp_id}/complete", json=comp_payload)
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "COMPLETED"

    # 5. Convert completed experiment to Knowledge Candidate
    resp4 = await api_client.post(f"/experiments/{exp_id}/promote")
    assert resp4.status_code == 200
    candidate = resp4.json()
    assert candidate["status"] == "CANDIDATE"
    assert "Query latency reduced by 42.5%" in candidate["statement"]
