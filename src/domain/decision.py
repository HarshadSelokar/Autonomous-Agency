"""
ManagerDecision Domain Entity for Persisted Organizational Decisions.
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


@dataclass
class ManagerDecision:
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
