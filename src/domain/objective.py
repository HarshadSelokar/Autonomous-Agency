"""
Organizational Objective Domain Entity & Lifecycle State Machine.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import InvalidStateTransitionError, ObjectiveValidationError


class ObjectiveStatus(str, Enum):
    RECEIVED = "RECEIVED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    CLARIFYING = "CLARIFYING"
    READY_FOR_PLANNING = "READY_FOR_PLANNING"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    EXECUTING = "EXECUTING"
    REVIEWING = "REVIEWING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


VALID_OBJECTIVE_TRANSITIONS: dict[ObjectiveStatus, set[ObjectiveStatus]] = {
    ObjectiveStatus.RECEIVED: {
        ObjectiveStatus.CLARIFICATION_REQUIRED,
        ObjectiveStatus.READY_FOR_PLANNING,
        ObjectiveStatus.PLANNING,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.CLARIFICATION_REQUIRED: {
        ObjectiveStatus.CLARIFYING,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.CLARIFYING: {
        ObjectiveStatus.READY_FOR_PLANNING,
        ObjectiveStatus.CLARIFICATION_REQUIRED,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.READY_FOR_PLANNING: {
        ObjectiveStatus.PLANNING,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.PLANNING: {
        ObjectiveStatus.PLANNED,
        ObjectiveStatus.CLARIFICATION_REQUIRED,
        ObjectiveStatus.FAILED,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.PLANNED: {
        ObjectiveStatus.EXECUTING,
        ObjectiveStatus.PLANNING,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.EXECUTING: {
        ObjectiveStatus.REVIEWING,
        ObjectiveStatus.BLOCKED,
        ObjectiveStatus.FAILED,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.REVIEWING: {
        ObjectiveStatus.COMPLETED,
        ObjectiveStatus.EXECUTING,
        ObjectiveStatus.BLOCKED,
        ObjectiveStatus.FAILED,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.BLOCKED: {
        ObjectiveStatus.EXECUTING,
        ObjectiveStatus.PLANNING,
        ObjectiveStatus.FAILED,
        ObjectiveStatus.CANCELLED,
    },
    ObjectiveStatus.COMPLETED: set(),
    ObjectiveStatus.FAILED: {ObjectiveStatus.READY_FOR_PLANNING, ObjectiveStatus.PLANNING},
    ObjectiveStatus.CANCELLED: set(),
}


@dataclass
class Objective:
    id: str
    title: str
    description: str
    requester: str
    priority: str = "medium"
    constraints: list[str] = field(default_factory=list)
    status: ObjectiveStatus = ObjectiveStatus.RECEIVED
    manager_id: str | None = None
    plan_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise ObjectiveValidationError("Objective ID cannot be empty.")
        if not self.title:
            raise ObjectiveValidationError("Objective title cannot be empty.")
        if not self.description:
            raise ObjectiveValidationError("Objective description cannot be empty.")
        if not self.requester:
            raise ObjectiveValidationError("Objective requester cannot be empty.")

    def can_transition_to(self, target_status: ObjectiveStatus) -> bool:
        allowed = VALID_OBJECTIVE_TRANSITIONS.get(self.status, set())
        return target_status in allowed

    def transition_to(self, target_status: ObjectiveStatus) -> None:
        if self.status == target_status:
            return

        if not self.can_transition_to(target_status):
            raise InvalidStateTransitionError(
                entity="Objective",
                entity_id=self.id,
                current_state=self.status.value,
                target_state=target_status.value,
            )

        self.status = target_status
        self.updated_at = datetime.now(UTC)
