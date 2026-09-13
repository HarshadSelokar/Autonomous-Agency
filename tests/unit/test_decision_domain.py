"""
Unit tests for evolved Decision domain model and state machine lifecycle.
"""

from datetime import UTC, datetime
import pytest

from src.domain.decision import (
    Decision,
    DecisionProvenance,
    DecisionStateError,
    DecisionStatus,
    DecisionType,
    DecisionValidationError,
    ManagerDecision,
)


def test_decision_creation_and_validation() -> None:
    decision = Decision(
        id="d-100",
        title="Choose Database Engine",
        question="Which database engine should be used for analytics?",
        decision_maker_employee_id="emp-mgr",
        decision_type=DecisionType.ARCHITECTURE,
        provenance=DecisionProvenance.EMPLOYEE,
        alternatives=["PostgreSQL", "ClickHouse", "MongoDB"],
    )
    assert decision.id == "d-100"
    assert decision.status == DecisionStatus.PROPOSED
    assert len(decision.alternatives) == 3


def test_decision_validation_empty_fields() -> None:
    with pytest.raises(DecisionValidationError, match="Decision ID cannot be empty"):
        Decision(id="", title="T", question="Q", decision_maker_employee_id="emp-1")

    with pytest.raises(DecisionValidationError, match="Decision title cannot be empty"):
        Decision(id="d-1", title="  ", question="Q", decision_maker_employee_id="emp-1")

    with pytest.raises(DecisionValidationError, match="Decision question cannot be empty"):
        Decision(id="d-1", title="T", question="", decision_maker_employee_id="emp-1")


def test_decision_lifecycle_transitions() -> None:
    decision = Decision(
        id="d-200",
        title="Select Gateway Architecture",
        question="Use Envoy or Kong?",
        decision_maker_employee_id="emp-dev",
    )
    assert decision.status == DecisionStatus.PROPOSED

    # PROPOSED -> UNDER_REVIEW
    decision.transition_to(DecisionStatus.UNDER_REVIEW)
    assert decision.status == DecisionStatus.UNDER_REVIEW

    # UNDER_REVIEW -> APPROVED
    decision.transition_to(
        DecisionStatus.APPROVED, approver_employee_id="emp-mgr", approver_role="Engineering Manager"
    )
    assert decision.status == DecisionStatus.APPROVED
    assert decision.approved_at is not None
    assert decision.decision_maker_employee_id == "emp-mgr"
    assert decision.approving_authority_role == "Engineering Manager"

    # APPROVED -> SUPERSEDED
    decision.transition_to(DecisionStatus.SUPERSEDED)
    assert decision.status == DecisionStatus.SUPERSEDED


def test_decision_invalid_transitions() -> None:
    decision = Decision(
        id="d-300",
        title="Invalid Transition Test",
        question="Question",
        decision_maker_employee_id="emp-1",
    )
    # Cannot jump from PROPOSED directly to APPROVED without UNDER_REVIEW
    with pytest.raises(DecisionStateError, match="Invalid decision transition"):
        decision.transition_to(DecisionStatus.APPROVED)


def test_legacy_manager_decision_mapping() -> None:
    legacy = ManagerDecision(
        id="md-1",
        manager_id="mgr-1",
        objective_id="obj-1",
        decision_type=DecisionType.APPROVE_PLAN,
        reasoning_summary="Plan matches capacity and capabilities",
        selected_action="Approve Architecture Plan",
        alternatives=["Reject Plan", "Request Clarification"],
    )
    mapped = legacy.to_organizational_decision()
    assert mapped.id == "md-1"
    assert mapped.status == DecisionStatus.APPROVED
    assert mapped.decision_maker_employee_id == "mgr-1"
    assert mapped.chosen_option == "Approve Architecture Plan"
    assert mapped.provenance == DecisionProvenance.MANAGER
