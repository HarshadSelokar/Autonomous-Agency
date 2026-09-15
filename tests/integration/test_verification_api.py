"""
Integration tests for Verification & Recovery REST APIs (Phase 10).
"""

import pytest
import src.infrastructure.models  # Register all ORM models
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


def test_verification_api_workflow(api_client):
    task_id = "task-api-100"

    # 1. Define Outcome
    outcome_payload = {
        "task_id": task_id,
        "description": "API Task Outcome",
        "criteria": ["File exists"],
        "rules": [
            {
                "rule_id": "r1",
                "rule_type": "FILE_VERIFICATION",
                "name": "Check config",
                "description": "Verify config.json exists",
                "target": "config.json",
                "expected_condition": {"exists": True},
                "severity": "CRITICAL",
                "retryable": True,
                "requires_human": False,
                "min_trust_level": "EXECUTED",
            }
        ],
    }
    resp1 = api_client.post("/verifications/outcomes", json=outcome_payload)
    assert resp1.status_code == 201
    assert resp1.json()["task_id"] == task_id

    # 2. Register Evidence
    ev_payload = {
        "source_type": "ToolExecution",
        "source_id": "te-api-1",
        "task_id": task_id,
        "trust_level": "EXECUTED",
        "payload": {"file": "config.json", "exists": True},
    }
    resp2 = api_client.post("/verifications/evidence", json=ev_payload)
    assert resp2.status_code == 201

    # 3. Verify Task
    resp3 = api_client.post("/verifications/verify", json={"task_id": task_id})
    assert resp3.status_code == 200
    res_data = resp3.json()
    assert res_data["status"] == "VERIFIED"
    assert res_data["task_id"] == task_id

    # 4. Get Verification
    v_id = res_data["verification_id"]
    resp4 = api_client.get(f"/verifications/{v_id}")
    assert resp4.status_code == 200
    assert resp4.json()["verification_id"] == v_id
