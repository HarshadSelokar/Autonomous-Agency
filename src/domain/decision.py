"""
Organizational Decision Domain Entity, Lifecycle, and Legacy ManagerDecision compatibility for Phase 6.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class DecisionType(str, Enum):
    APPROVE_PLAN = "APPROVE_PLAN"
    REJECT_PLAN = "REJECT_PLAN"
    ASSIGN_WORK = "ASSIGN_WORK"
    REASSIGN_WORK = "REASSIGN_WORK"
    CLARIFY_OBJECTIVE = "CLARIFY_OBJECTIVE"
    RESOLVE_BLOCKER = "RESOLVE_BLOCKER"
    ESCALATE = "ESCALATE"
    APPROVE_RESULT = "APPROVE_RESULT"
    ARCHITECTURE = "ARCHITECTURE"
    POLICY = "POLICY"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    GENERAL = "GENERAL"


class DecisionStatus(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


class DecisionProvenance(str, Enum):
    HUMAN = "HUMAN"
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    AGENT_ASSISTED = "AGENT_ASSISTED"
    SYSTEM_PROPOSAL = "SYSTEM_PROPOSAL"


class DecisionValidationError(ObjectiveValidationError):
    """Raised when decision domain constraints or state transitions are violated."""

    pass


class DecisionStateError(DecisionValidationError):
    """Raised when an invalid decision lifecycle transition is attempted."""

    pass


VALID_DECISION_TRANSITIONS: dict[DecisionStatus, set[DecisionStatus]] = {
    DecisionStatus.PROPOSED: {DecisionStatus.UNDER_REVIEW, DecisionStatus.CANCELLED},
    DecisionStatus.UNDER_REVIEW: {DecisionStatus.APPROVED, DecisionStatus.REJECTED, DecisionStatus.CANCELLED},
    DecisionStatus.APPROVED: {DecisionStatus.SUPERSEDED, DecisionStatus.CANCELLED},
    DecisionStatus.REJECTED: set(),
    DecisionStatus.SUPERSEDED: set(),
    DecisionStatus.CANCELLED: set(),
}


@dataclass
class Decision:
    id: str
    title: str
    question: str
    decision_maker_employee_id: str
    description: str | None = None
    status: DecisionStatus = DecisionStatus.PROPOSED
    decision_type: DecisionType = DecisionType.GENERAL
    approving_authority_role: str | None = None
    chosen_option: str | None = None
    alternatives: list[str] = field(default_factory=list)
    rationale: str | None = None
    consequences: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    meeting_id: str | None = None
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    previous_decision_id: str | None = None
    provenance: DecisionProvenance = DecisionProvenance.EMPLOYEE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    approved_at: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise DecisionValidationError("Decision ID cannot be empty.")
        if not self.title or not self.title.strip():
            raise DecisionValidationError("Decision title cannot be empty.")
        if not self.question or not self.question.strip():
            raise DecisionValidationError("Decision question cannot be empty.")
        if not self.decision_maker_employee_id or not self.decision_maker_employee_id.strip():
            raise DecisionValidationError("Decision decision_maker_employee_id cannot be empty.")

    def transition_to(
        self,
        target_status: DecisionStatus,
        approver_employee_id: str | None = None,
        approver_role: str | None = None,
    ) -> None:
        """Execute a deterministic state transition."""
        allowed = VALID_DECISION_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise DecisionStateError(
                f"Invalid decision transition from {self.status.value} to {target_status.value}."
            )

        now = datetime.now(UTC)
        if target_status == DecisionStatus.APPROVED:
            self.approved_at = now
            if approver_employee_id:
                self.decision_maker_employee_id = approver_employee_id
            if approver_role:
                self.approving_authority_role = approver_role

        self.status = target_status
        self.updated_at = now


@dataclass
class ManagerDecision:
    """Phase 3 Legacy ManagerDecision domain entity for backward compatibility."""

    id: str
    manager_id: str
    objective_id: str
    decision_type: DecisionType
    reasoning_summary: str
    selected_action: str
    alternatives: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise ObjectiveValidationError("ManagerDecision ID cannot be empty.")
        if not self.manager_id:
            raise ObjectiveValidationError("ManagerDecision manager_id cannot be empty.")
        if not self.objective_id:
            raise ObjectiveValidationError("ManagerDecision objective_id cannot be empty.")
        if not self.reasoning_summary:
            raise ObjectiveValidationError("ManagerDecision reasoning_summary cannot be empty.")
        if not self.selected_action:
            raise ObjectiveValidationError("ManagerDecision selected_action cannot be empty.")

    def to_organizational_decision(self) -> Decision:
        """Map legacy ManagerDecision to full Phase 6 Decision."""
        return Decision(
            id=self.id,
            title=f"Manager Decision: {self.decision_type.value}",
            question=f"Manager Action for Objective {self.objective_id}",
            decision_maker_employee_id=self.manager_id,
            status=DecisionStatus.APPROVED,
            decision_type=self.decision_type,
            chosen_option=self.selected_action,
            alternatives=self.alternatives,
            rationale=self.reasoning_summary,
            objective_id=self.objective_id,
            provenance=DecisionProvenance.MANAGER,
            metadata=self.metadata,
            created_at=self.created_at,
            approved_at=self.created_at,
        )
