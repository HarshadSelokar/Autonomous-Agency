"""
Integration tests for Human Governance REST APIs (Phase 11).
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


def test_governance_policy_and_approval_api_workflow(api_client):
    # 1. Define Policy
    policy_payload = {
        "name": "Production Deploy Policy",
        "scope": "PROJECT",
        "scope_id": "proj-101",
        "level": "PROJECT",
        "rules": [
            {
                "rule_id": "rule-prod-deploy",
                "name": "Deploy Approval",
                "description": "Deployment requires manager approval",
                "scope": "PROJECT",
                "target_pattern": "deploy_*",
                "min_risk_level": "HIGH",
                "autonomy_level": "APPROVAL_REQUIRED",
                "required_approver_roles": ["MANAGER"],
                "prohibit_self_approval": True,
                "approval_validity_seconds": 3600,
                "allow_override": True,
            }
        ],
    }
    resp1 = api_client.post("/governance/policies", json=policy_payload)
    assert resp1.status_code == 201
    assert "policy_id" in resp1.json()

    # 2. Request Approval
    approval_payload = {
        "action_type": "deploy_prod",
        "action_target": "production-cluster",
        "requested_by_actor_id": "emp-agent-1",
        "task_id": "task-deploy-1",
        "project_id": "proj-101",
        "risk_level": "HIGH",
        "required_approver_roles": ["MANAGER"],
        "prohibit_self_approval": True,
        "validity_seconds": 3600,
        "payload": {"version": "v1.2.3"},
    }
    resp2 = api_client.post("/governance/approvals", json=approval_payload)
    assert resp2.status_code == 201
    req_data = resp2.json()
    req_id = req_data["request_id"]
    assert req_data["status"] == "PENDING"
    assert req_data["requested_by_actor_id"] == "emp-agent-1"

    # 3. Test self-approval prevention (HTTP 400)
    resp3_fail = api_client.post(
        f"/governance/approvals/{req_id}/approve",
        json={"actor_id": "emp-agent-1"},
    )
    assert resp3_fail.status_code == 400
    assert "Self-approval prohibited" in resp3_fail.json()["detail"]

    # 4. Approve request with valid manager actor
    resp3 = api_client.post(
        f"/governance/approvals/{req_id}/approve",
        json={"actor_id": "emp-mgr-2"},
    )
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "APPROVED"
    assert resp3.json()["approved_by_actor_id"] == "emp-mgr-2"


def test_governance_emergency_stop_and_violations_api(api_client):
    # 1. Emergency Stop
    stop_payload = {
        "activated_by_actor_id": "admin-1",
        "reason": "Security Breach Alert",
        "scope": "GLOBAL",
        "scope_id": "GLOBAL",
    }
    resp1 = api_client.post("/governance/stop", json=stop_payload)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "ACTIVATED"

    # 2. Record Intervention
    intv_payload = {
        "intervention_type": "KILL_SWITCH_ACTIVATED",
        "scope": "GLOBAL",
        "scope_id": "GLOBAL",
        "actor_id": "admin-1",
        "reason": "Shutting down system due to alert",
        "details": {"alert_id": "ALT-999"},
    }
    resp2 = api_client.post("/governance/interventions", json=intv_payload)
    assert resp2.status_code == 201
    assert resp2.json()["status"] == "RECORDED"

    # 3. List Violations
    resp3 = api_client.get("/governance/violations")
    assert resp3.status_code == 200
    assert isinstance(resp3.json(), list)
