"""
AgentRun Domain Entity and Lifecycle State Machine.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import InvalidStateTransitionError


class RunStatus(str, Enum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


VALID_RUN_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.CREATED: {RunStatus.INITIALIZING, RunStatus.CANCELLED, RunStatus.FAILED},
    RunStatus.INITIALIZING: {RunStatus.RUNNING, RunStatus.CANCELLED, RunStatus.FAILED},
    RunStatus.RUNNING: {
        RunStatus.WAITING,
        RunStatus.COMPLETED,
        RunStatus.FAILED,
        RunStatus.CANCELLED,
    },
    RunStatus.WAITING: {RunStatus.RUNNING, RunStatus.FAILED, RunStatus.CANCELLED},
    RunStatus.COMPLETED: set(),
    RunStatus.FAILED: set(),
    RunStatus.CANCELLED: set(),
}


@dataclass
class AgentRun:
    id: str
    agent_id: str
    objective: str
    status: RunStatus = RunStatus.CREATED
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_reason: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def can_transition_to(self, target_status: RunStatus) -> bool:
        """Check if transition to target_status is valid."""
        allowed = VALID_RUN_TRANSITIONS.get(self.status, set())
        return target_status in allowed

    def transition_to(self, target_status: RunStatus, failure_reason: str | None = None) -> None:
        """
        Transition run status to target_status if valid, updating timestamps accordingly.
        """
        if self.status == target_status:
            return

        if not self.can_transition_to(target_status):
            raise InvalidStateTransitionError(
                entity="AgentRun",
                entity_id=self.id,
                current_state=self.status.value,
                target_state=target_status.value,
            )

        self.status = target_status
        now = datetime.now(UTC)
        self.updated_at = now

        if target_status == RunStatus.RUNNING and self.started_at is None:
            self.started_at = now

        if target_status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            self.completed_at = now
            if failure_reason is not None:
                self.failure_reason = failure_reason
