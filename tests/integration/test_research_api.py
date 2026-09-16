"""Integration tests for Phase 19 Research, Discovery & Innovation API endpoints."""

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
async def test_research_and_innovation_api_flow(api_client: AsyncClient):
    # 1. Create Research Request
    req_payload = {
        "question": "How can we optimize vector search latency for organization memory?",
        "purpose": "Improve context retrieval performance",
        "scope": "COMPANY",
        "urgency": "HIGH",
        "requester_id": "emp-cto-01",
        "source_origin": "STRATEGY",
        "governance_required": True,
    }
    r_req = await api_client.post("/api/v1/research/requests", json=req_payload)
    assert r_req.status_code == 201
    req_data = r_req.json()
    req_id = req_data["id"]
    assert req_data["question"] == req_payload["question"]

    # 2. Decompose Request
    r_decomp = await api_client.post(
        f"/api/v1/research/requests/{req_id}/decompose",
        json={"sub_questions": ["What index type yields highest recall?", "What is memory overhead?"]},
    )
    assert r_decomp.status_code == 200
    decomp_data = r_decomp.json()
    assert decomp_data["question_count"] == 3
    main_q_id = decomp_data["questions"][0]["id"]

    # 3. Create Research Plan
    plan_payload = {
        "question_id": main_q_id,
        "title": "HNSW vs IVFFlat Benchmark Plan",
        "objective": "Benchmark retrieval latency across 1M vectors",
        "required_capabilities": ["vector_db", "benchmarking"],
    }
    r_plan = await api_client.post("/api/v1/research/plans", json=plan_payload)
    assert r_plan.status_code == 201

    # 4. Register Source
    src_payload = {
        "location": "https://arxiv.org/abs/2301.99999",
        "source_type": "PUBLIC_RESEARCH_PAPER",
        "provenance": "ArXiv Vector Search Benchmark",
        "raw_content": "HNSW index provides 5x faster retrieval at 98% recall.",
        "is_external": True,
    }
    r_src = await api_client.post("/api/v1/research/sources", json=src_payload)
    assert r_src.status_code == 201
    src_data = r_src.json()
    src_id = src_data["id"]
    assert src_data["is_untrusted"] is True
    assert src_data["reliability_score"] > 0.0

    # 5. Add Evidence
    ev_payload = {
        "source_id": src_id,
        "content_snippet": "HNSW index provides 5x faster retrieval at 98% recall.",
        "data_points": {"speedup": 5.0, "recall": 0.98},
    }
    r_ev = await api_client.post("/api/v1/research/evidence", json=ev_payload)
    assert r_ev.status_code == 201
    ev_data = r_ev.json()
    ev_id = ev_data["id"]

    # 6. Synthesize Finding
    find_payload = {
        "question_id": main_q_id,
        "finding_statement": "HNSW index offers superior speedup and recall over IVFFlat.",
        "evidence_ids": [ev_id],
        "confidence": 0.92,
        "researcher_id": "emp-ai-lead",
    }
    r_find = await api_client.post("/api/v1/research/findings", json=find_payload)
    assert r_find.status_code == 201
    find_data = r_find.json()
    find_id = find_data["id"]

    # 7. Formulate and Evaluate Hypothesis
    hyp_payload = {
        "question_id": main_q_id,
        "observation": "Vector retrieval is bottlenecking memory queries",
        "statement": "Switching to HNSW index will cut memory retrieval time in half",
        "prediction": "50% latency reduction",
    }
    r_hyp = await api_client.post("/api/v1/research/hypotheses", json=hyp_payload)
    assert r_hyp.status_code == 201
    hyp_id = r_hyp.json()["id"]

    eval_payload = {
        "result_description": "Empirical benchmark showed 60% latency reduction.",
        "conclusion": "HNSW vector indexing improves query speed by 2.5x.",
        "is_supported": True,
    }
    r_eval = await api_client.post(f"/api/v1/research/hypotheses/{hyp_id}/evaluate", json=eval_payload)
    assert r_eval.status_code == 200
    assert r_eval.json()["promoted_to_knowledge"] is True

    # 8. Identify Opportunity & Create Innovation Proposal
    opp_payload = {
        "finding_id": find_id,
        "title": "HNSW Vector Engine Upgrade",
        "description": "Upgrade organization memory vector engine to HNSW",
        "estimated_value_score": 0.95,
    }
    r_opp = await api_client.post("/api/v1/innovation/opportunities", json=opp_payload)
    assert r_opp.status_code == 201
    opp_id = r_opp.json()["id"]

    prop_payload = {
        "opportunity_id": opp_id,
        "title": "Phase 19 HNSW Memory Accelerator",
        "innovation_type": "ARCHITECTURE_INNOVATION",
        "problem_statement": "High latency in memory context retrieval",
        "proposed_solution": "Deploy HNSW vector indexer service",
        "expected_value": "2.5x query throughput increase",
        "evidence_ids": [ev_id],
        "reversibility": "HIGH",
    }
    r_prop = await api_client.post("/api/v1/innovation/proposals", json=prop_payload)
    assert r_prop.status_code == 201
    prop_id = r_prop.json()["id"]
    assert r_prop.json()["is_approved"] is False

    # 9. Approve Innovation Proposal via Governance
    appr_payload = {
        "governance_request_id": "gov-req-12345",
    }
    r_appr = await api_client.post(f"/api/v1/innovation/proposals/{prop_id}/approve", json=appr_payload)
    assert r_appr.status_code == 200
    appr_data = r_appr.json()
    assert appr_data["is_approved"] is True
    assert appr_data["strategic_initiative_id"].startswith("init-inno-")
