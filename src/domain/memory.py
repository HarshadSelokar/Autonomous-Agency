"""
MemoryEntry Domain Entity, Memory Types, Scopes, Authority Levels, and Lifecycle for Phase 7.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class MemoryType(str, Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    ORGANIZATIONAL = "ORGANIZATIONAL"


class MemoryScope(str, Enum):
    RUN = "RUN"
    TASK = "TASK"
    EMPLOYEE = "EMPLOYEE"
    PROJECT = "PROJECT"
    DEPARTMENT = "DEPARTMENT"
    COMPANY = "COMPANY"


class MemoryAuthority(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    OBSERVED = "OBSERVED"
    GENERATED = "GENERATED"
    CONFIRMED = "CONFIRMED"
    AUTHORITATIVE = "AUTHORITATIVE"


class MemoryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"
    INVALIDATED = "INVALIDATED"


class MemoryProvenance(str, Enum):
    AGENT_RUN = "AGENT_RUN"
    MESSAGE = "MESSAGE"
    MEETING = "MEETING"
    DECISION = "DECISION"
    TASK = "TASK"
    ARTIFACT = "ARTIFACT"
    EMPLOYEE = "EMPLOYEE"
    SYSTEM_EVENT = "SYSTEM_EVENT"


class MemoryValidationError(ObjectiveValidationError):
    """Raised when memory domain invariants or scope constraints are violated."""

    pass


class MemoryStateError(MemoryValidationError):
    """Raised when an invalid memory lifecycle transition is attempted."""

    pass


VALID_MEMORY_TRANSITIONS: dict[MemoryStatus, set[MemoryStatus]] = {
    MemoryStatus.ACTIVE: {MemoryStatus.SUPERSEDED, MemoryStatus.ARCHIVED, MemoryStatus.INVALIDATED},
    MemoryStatus.ARCHIVED: {MemoryStatus.ACTIVE, MemoryStatus.INVALIDATED},
    MemoryStatus.SUPERSEDED: set(),
    MemoryStatus.INVALIDATED: set(),
}


@dataclass
class MemoryEntry:
    id: str
    memory_type: MemoryType
    scope: MemoryScope
    owner_id: str
    content: str
    summary: str | None = None
    authority: MemoryAuthority = MemoryAuthority.GENERATED
    confidence: float = 0.5
    provenance: MemoryProvenance = MemoryProvenance.AGENT_RUN
    source_id: str | None = None
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    employee_id: str | None = None
    agent_run_id: str | None = None
    meeting_id: str | None = None
    decision_id: str | None = None
    artifact_id: str | None = None
    previous_memory_id: str | None = None
    embedding: list[float] | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise MemoryValidationError("Memory ID cannot be empty.")
        if not self.owner_id or not self.owner_id.strip():
            raise MemoryValidationError("Memory owner_id cannot be empty.")
        if not self.content or not self.content.strip():
            raise MemoryValidationError("Memory content cannot be empty.")
        if not (0.0 <= self.confidence <= 1.0):
            raise MemoryValidationError("Memory confidence must be between 0.0 and 1.0.")

    def transition_to(self, target_status: MemoryStatus) -> None:
        """Execute a deterministic state transition."""
        allowed = VALID_MEMORY_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise MemoryStateError(
                f"Invalid memory transition from {self.status.value} to {target_status.value}."
            )

        self.status = target_status
        self.updated_at = datetime.now(UTC)
