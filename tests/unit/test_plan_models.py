"""
Unit tests for Plan, WorkItem, Assignment, and ManagerDecision domain entities.
"""

import pytest

from src.domain.assignment import Assignment, AssignmentStatus
from src.domain.decision import DecisionType, ManagerDecision
from src.domain.exceptions import AssignmentError, ObjectiveValidationError, PlanValidationError
from src.domain.plan import Plan, PlanStatus
from src.domain.work_item import WorkItem, WorkItemStatus


def test_work_item_creation_and_validation() -> None:
    wi = WorkItem(
        id="wi_100",
        plan_id="plan_001",
        title="Implement Backend API",
        description="Write FastAPI endpoints",
        required_capabilities=["python", "fastapi"],
    )
    assert wi.id == "wi_100"
    assert wi.status == WorkItemStatus.PLANNED
    assert wi.required_capabilities == ["python", "fastapi"]


def test_work_item_validation_error() -> None:
    with pytest.raises(ObjectiveValidationError) as exc:
        WorkItem(id="", plan_id="p1", title="T", description="D")
    assert "WorkItem ID cannot be empty" in str(exc.value)


def test_plan_creation_and_validation() -> None:
    wi = WorkItem(
        id="wi_101",
        plan_id="plan_001",
        title="Setup DB",
        description="Migrate DB schema",
    )
    plan = Plan(
        id="plan_001",
        objective_id="obj_001",
        manager_id="emp_mgr_01",
        goals=["Deliver Phase 3"],
        work_items=[wi],
        status=PlanStatus.DRAFT,
    )

    assert plan.id == "plan_001"
    assert plan.status == PlanStatus.DRAFT
    assert len(plan.work_items) == 1


def test_plan_validation_error() -> None:
    with pytest.raises(PlanValidationError) as exc:
        Plan(id="", objective_id="obj1", manager_id="mgr1")
    assert "Plan ID cannot be empty" in str(exc.value)


def test_assignment_creation_and_validation() -> None:
    assign = Assignment(
        id="asgn_001",
        work_item_id="wi_100",
        employee_id="emp_alice",
        assigned_by="emp_bob_mgr",
        reason="Primary developer for backend API",
        status=AssignmentStatus.ACTIVE,
    )
    assert assign.id == "asgn_001"
    assert assign.status == AssignmentStatus.ACTIVE


def test_assignment_validation_error() -> None:
    with pytest.raises(AssignmentError) as exc:
        Assignment(id="", work_item_id="wi1", employee_id="emp1", assigned_by="mgr1")
    assert "Assignment ID cannot be empty" in str(exc.value)


def test_manager_decision_creation_and_validation() -> None:
    decision = ManagerDecision(
        id="dec_001",
        manager_id="emp_bob_mgr",
        objective_id="obj_001",
        decision_type=DecisionType.APPROVE_PLAN,
        reasoning_summary="Plan is feasible and resource capabilities match requirements",
        selected_action="Approve plan and begin work item assignment",
        alternatives=["Request more resources", "Reject plan"],
    )
    assert decision.id == "dec_001"
    assert decision.decision_type == DecisionType.APPROVE_PLAN
