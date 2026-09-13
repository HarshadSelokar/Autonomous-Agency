"""
Meeting Domain Entity and Lifecycle for Phase 6 Meetings & Decision Management.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class MeetingPurpose(str, Enum):
    PLANNING = "PLANNING"
    STATUS = "STATUS"
    REVIEW = "REVIEW"
    DECISION = "DECISION"
    BLOCKER_RESOLUTION = "BLOCKER_RESOLUTION"
    INCIDENT = "INCIDENT"
    COORDINATION = "COORDINATION"


class MeetingStatus(str, Enum):
    PROPOSED = "PROPOSED"
    SCHEDULED = "SCHEDULED"
    STARTING = "STARTING"
    IN_PROGRESS = "IN_PROGRESS"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class MeetingValidationError(ObjectiveValidationError):
    """Raised when meeting domain constraints or state transitions are violated."""

    pass


class MeetingStateError(MeetingValidationError):
    """Raised when an invalid meeting lifecycle transition is attempted."""

    pass


VALID_MEETING_TRANSITIONS: dict[MeetingStatus, set[MeetingStatus]] = {
    MeetingStatus.PROPOSED: {MeetingStatus.SCHEDULED, MeetingStatus.CANCELLED},
    MeetingStatus.SCHEDULED: {MeetingStatus.STARTING, MeetingStatus.CANCELLED},
    MeetingStatus.STARTING: {MeetingStatus.IN_PROGRESS, MeetingStatus.CANCELLED},
    MeetingStatus.IN_PROGRESS: {MeetingStatus.ENDED, MeetingStatus.CANCELLED},
    MeetingStatus.ENDED: set(),
    MeetingStatus.CANCELLED: set(),
}


@dataclass
class Meeting:
    id: str
    title: str
    purpose: MeetingPurpose
    organizer_employee_id: str
    status: MeetingStatus = MeetingStatus.PROPOSED
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    conversation_id: str | None = None
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise MeetingValidationError("Meeting ID cannot be empty.")
        if not self.title or not self.title.strip():
            raise MeetingValidationError("Meeting title cannot be empty.")
        if not self.organizer_employee_id or not self.organizer_employee_id.strip():
            raise MeetingValidationError("Meeting organizer_employee_id cannot be empty.")
        if self.scheduled_start and self.scheduled_end:
            if self.scheduled_end <= self.scheduled_start:
                raise MeetingValidationError("scheduled_end must be strictly after scheduled_start.")

    def transition_to(self, target_status: MeetingStatus) -> None:
        """Execute a deterministic state transition."""
        allowed = VALID_MEETING_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise MeetingStateError(
                f"Invalid meeting transition from {self.status.value} to {target_status.value}."
            )
        now = datetime.now(UTC)
        if target_status == MeetingStatus.STARTING and self.actual_start is None:
            self.actual_start = now
        elif target_status == MeetingStatus.IN_PROGRESS and self.actual_start is None:
            self.actual_start = now
        elif target_status == MeetingStatus.ENDED:
            self.actual_end = now
        self.status = target_status
        self.updated_at = now
