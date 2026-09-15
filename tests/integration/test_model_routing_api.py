"""
Integration tests for Model Routing REST APIs (Phase 12).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.infrastructure.database import Base, get_db


@pytest.fixture
def api_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_model_routing_api_workflow(api_client):
    # 1. Register Model Profile
    profile_payload = {
        "model_id": "llama-3.3-70b-versatile",
        "provider_name": "Groq",
        "model_name": "Llama 3.3 70B",
        "capabilities": ["TEXT_GENERATION", "CODE_GENERATION", "REASONING"],
        "context_window_tokens": 128000,
        "cost_per_1k_input_tokens": 0.00059,
        "cost_per_1k_output_tokens": 0.00079,
        "latency_ms": 350.0,
        "quality_score": 0.92,
        "is_active": True,
        "is_approved_for_production": True,
    }
    resp1 = api_client.post("/models", json=profile_payload)
    assert resp1.status_code == 201
    assert resp1.json()["model_id"] == "llama-3.3-70b-versatile"
    assert resp1.json()["status"] == "REGISTERED"

    # 2. Update Provider Health
    health_payload = {
        "provider_name": "Groq",
        "model_id": "llama-3.3-70b-versatile",
        "is_healthy": True,
        "error_rate": 0.001,
        "latency_p95_ms": 400.0,
    }
    resp2 = api_client.post("/models/health", json=health_payload)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "UPDATED"
    assert resp2.json()["is_healthy"] == "True"

    # 3. Route Model Request
    route_payload = {
        "task_id": "task-api-route-1",
        "agent_id": "agent-dev-1",
        "required_capabilities": ["TEXT_GENERATION", "CODE_GENERATION"],
        "strategy": "CAPABILITY_BASED",
        "min_quality_score": 0.8,
    }
    resp3 = api_client.post("/models/route", json=route_payload)
    assert resp3.status_code == 200
    decision = resp3.json()
    assert decision["selected_model_id"] == "llama-3.3-70b-versatile"
    assert decision["selected_provider_name"] == "Groq"
    assert decision["strategy_used"] == "CAPABILITY_BASED"
