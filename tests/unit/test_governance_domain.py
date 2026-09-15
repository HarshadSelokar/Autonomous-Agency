"""
Unit tests for Governance Domain Model (Phase 11).
"""

import pytest
from datetime import datetime, timedelta, timezone
from src.domain.governance import (
    ApprovalStatus,
    AutonomyLevel,
    GovernanceApprovalRequest,
    GovernancePolicy,
    GovernanceRule,
    GovernanceScope,
    RiskLevel,
)


def test_governance_policy_precedence():
    p_task = GovernancePolicy(policy_id="p1", name="Task Policy", scope=GovernanceScope.TASK, level="TASK")
    p_dept = GovernancePolicy(policy_id="p2", name="Dept Policy", scope=GovernanceScope.DEPARTMENT, level="DEPARTMENT")
    p_sys = GovernancePolicy(policy_id="p3", name="System Policy", scope=GovernanceScope.GLOBAL, level="SYSTEM")

    assert p_sys.precedence_order > p_dept.precedence_order
    assert p_dept.precedence_order > p_task.precedence_order


def test_approval_request_expiration():
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    req_active = GovernanceApprovalRequest(
        request_id="r1",
        action_type="DEPLOYMENT",
        action_target="prod-cluster",
        requested_by_actor_id="emp-dev-1",
        expires_at=future_time,
    )
    assert not req_active.is_expired()

    past_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    req_expired = GovernanceApprovalRequest(
        request_id="r2",
        action_type="DEPLOYMENT",
        action_target="prod-cluster",
        requested_by_actor_id="emp-dev-1",
        expires_at=past_time,
    )
    assert req_expired.is_expired()
