"""
Unit tests for DecisionAuthorityService and approval authority validation.
"""

from datetime import UTC, datetime
import pytest

from src.application.decision_authority_service import (
    DecisionAuthorityService,
    UnauthorizedDecisionApprovalError,
)
from src.domain.decision import Decision, DecisionProvenance, DecisionStatus, DecisionType
from src.domain.employee import Employee, EmployeeStatus
from tests.unit.test_meeting_scheduling import MemoryEmployeeRepository


@pytest.mark.asyncio
async def test_approve_decision_success() -> None:
    employee_repo = MemoryEmployeeRepository()
    mgr = Employee(
        id="emp-mgr",
        name="Bob Manager",
        role="Manager",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_MGR",
        title="Engineering Manager",
        agent_id="agent-mgr",
    )
    await employee_repo.save(mgr)

    service = DecisionAuthorityService(employee_repo=employee_repo)

    decision = Decision(
        id="d-auth-1",
        title="Adopt FastAPI",
        question="Use FastAPI for backend framework?",
        decision_maker_employee_id="emp-dev",
        approving_authority_role="Manager",
    )

    approved = await service.approve_decision(
        decision=decision, approver_employee_id="emp-mgr"
    )
    assert approved.status == DecisionStatus.APPROVED
    assert approved.decision_maker_employee_id == "emp-mgr"
    assert approved.approved_at is not None


@pytest.mark.asyncio
async def test_approve_decision_unauthorized_role_rejected() -> None:
    employee_repo = MemoryEmployeeRepository()
    dev = Employee(
        id="emp-dev",
        name="Alice Dev",
        role="Junior Developer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_DEV",
        title="Junior Software Engineer",
        agent_id="agent-dev",
    )
    await employee_repo.save(dev)

    service = DecisionAuthorityService(employee_repo=employee_repo)

    decision = Decision(
        id="d-auth-2",
        title="Production Deployment",
        question="Deploy v2.0 to production?",
        decision_maker_employee_id="emp-dev",
        approving_authority_role="Engineering Manager",
    )

    with pytest.raises(UnauthorizedDecisionApprovalError, match="lacks required approving authority role"):
        await service.approve_decision(decision=decision, approver_employee_id="emp-dev")

    assert decision.status == DecisionStatus.PROPOSED


@pytest.mark.asyncio
async def test_reject_decision_authorized() -> None:
    employee_repo = MemoryEmployeeRepository()
    mgr = Employee(
        id="emp-mgr",
        name="Bob Manager",
        role="Manager",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_MGR",
        title="Engineering Manager",
        agent_id="agent-mgr",
    )
    await employee_repo.save(mgr)

    service = DecisionAuthorityService(employee_repo=employee_repo)

    decision = Decision(
        id="d-auth-3",
        title="Use Custom Framework",
        question="Build in-house framework?",
        decision_maker_employee_id="emp-dev",
    )

    rejected = await service.reject_decision(
        decision=decision,
        approver_employee_id="emp-mgr",
        reason="High maintenance overhead",
    )
    assert rejected.status == DecisionStatus.REJECTED
    assert "High maintenance overhead" in (rejected.rationale or "")
