"""
Integration tests for GovernanceRepository (Phase 11).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.models  # noqa: F401
from src.domain.governance import (
    ApprovalStatus,
    AutonomyLevel,
    EmergencyStopState,
    GovernanceApprovalRequest,
    GovernancePolicy,
    GovernanceRule,
    GovernanceScope,
    HumanIntervention,
    RiskLevel,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.governance_repository import GovernanceRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_governance_repository_policy_and_approvals(db_session):
    repo = GovernanceRepository(db_session)

    # 1. Policy
    rule = GovernanceRule(
        rule_id="r1",
        name="Production Deploy Rule",
        description="Requires human approval",
        scope=GovernanceScope.GLOBAL,
        target_pattern="tool:deploy*",
        min_risk_level=RiskLevel.HIGH,
        autonomy_level=AutonomyLevel.APPROVAL_REQUIRED,
    )
    policy = GovernancePolicy(
        policy_id="pol-1",
        name="Company Security Policy",
        scope=GovernanceScope.COMPANY,
        level="COMPANY",
        rules=[rule],
    )
    repo.save_policy(policy)
    p_fetched = repo.get_policy("pol-1")
    assert p_fetched is not None
    assert p_fetched.name == "Company Security Policy"

    # 2. Approval Request
    req = GovernanceApprovalRequest(
        request_id="req-1",
        action_type="DEPLOYMENT",
        action_target="prod-cluster",
        requested_by_actor_id="emp-dev-1",
        risk_level=RiskLevel.HIGH,
        status=ApprovalStatus.PENDING,
    )
    repo.save_approval_request(req)
    req_fetched = repo.get_approval_request("req-1")
    assert req_fetched is not None
    assert req_fetched.action_type == "DEPLOYMENT"

    # 3. Emergency Stop
    stop = EmergencyStopState(
        stop_id="stop-1",
        scope=GovernanceScope.GLOBAL,
        scope_id="GLOBAL",
        activated_by_actor_id="emp-vp-eng",
        reason="System security audit",
        is_active=True,
    )
    repo.save_emergency_stop(stop)
    stops = repo.get_active_emergency_stops()
    assert len(stops) == 1
    assert stops[0].scope_id == "GLOBAL"
