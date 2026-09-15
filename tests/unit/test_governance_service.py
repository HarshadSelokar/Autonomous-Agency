"""
Unit tests for GovernanceService (Phase 11).
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.models  # noqa: F401
from src.application.governance_service import GovernanceService
from src.domain.governance import (
    ApprovalStatus,
    AutonomyLevel,
    GovernanceRule,
    GovernanceScope,
    RiskLevel,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository


@pytest.fixture
def governance_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = GovernanceRepository(session)
    return GovernanceService(repository=repo)


def test_classify_risk_level(governance_service):
    r_prod = governance_service.classify_action_risk("DEPLOY", "prod-database-cluster")
    assert r_prod == RiskLevel.CRITICAL

    r_fin = governance_service.classify_action_risk("FINANCIAL_TRANSFER", "bank-account")
    assert r_fin == RiskLevel.HIGH

    r_write = governance_service.classify_action_risk("UPDATE_PROFILE", "user-settings")
    assert r_write == RiskLevel.MEDIUM

    r_low = governance_service.classify_action_risk("READ", "public-docs")
    assert r_low == RiskLevel.LOW


def test_emergency_stop_kill_switch(governance_service):
    # Before emergency stop
    autonomy1, risk1, _ = governance_service.evaluate_autonomy("READ", "docs", "actor-1")
    assert autonomy1 == AutonomyLevel.FULLY_AUTONOMOUS

    # Activate Global Emergency Stop
    stop = governance_service.activate_emergency_stop("emp-admin", "Security Audit in progress")
    assert stop.is_active

    # After emergency stop -> All actions must be BLOCKED
    autonomy2, risk2, _ = governance_service.evaluate_autonomy("READ", "docs", "actor-1")
    assert autonomy2 == AutonomyLevel.BLOCKED

    # Deactivate Emergency Stop
    governance_service.deactivate_emergency_stop(stop.stop_id, "emp-admin")
    autonomy3, risk3, _ = governance_service.evaluate_autonomy("READ", "docs", "actor-1")
    assert autonomy3 == AutonomyLevel.FULLY_AUTONOMOUS


def test_approval_workflow_and_self_approval_prevention(governance_service):
    # Request Approval for High-Risk action
    req = governance_service.request_approval(
        action_type="DEPLOYMENT",
        action_target="prod-cluster",
        requested_by_actor_id="emp-dev-100",
        risk_level=RiskLevel.HIGH,
    )
    assert req.status == ApprovalStatus.PENDING

    # Self-approval MUST fail due to separation of duties
    with pytest.raises(ValueError, match="Self-approval prohibited"):
        governance_service.approve_request(req.request_id, approver_actor_id="emp-dev-100")

    # Independent Manager approves
    approved_req = governance_service.approve_request(req.request_id, approver_actor_id="emp-mgr-200")
    assert approved_req.status == ApprovalStatus.APPROVED
    assert approved_req.approved_by_actor_id == "emp-mgr-200"
