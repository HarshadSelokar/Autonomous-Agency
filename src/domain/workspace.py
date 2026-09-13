"""
Workspace Domain Entity, Types, Scopes, and Lifecycle State Machine for Phase 7.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class WorkspaceType(str, Enum):
    TASK = "TASK"
    PROJECT = "PROJECT"
    EMPLOYEE = "EMPLOYEE"
    AGENT = "AGENT"
    SHARED = "SHARED"


class WorkspaceStatus(str, Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    ARCHIVED = "ARCHIVED"
    DESTROYED = "DESTROYED"


class WorkspaceValidationError(ObjectiveValidationError):
    """Raised when workspace domain invariants are violated."""

    pass


class WorkspaceStateError(WorkspaceValidationError):
    """Raised when an invalid workspace state transition is attempted."""

    pass


VALID_WORKSPACE_TRANSITIONS: dict[WorkspaceStatus, set[WorkspaceStatus]] = {
    WorkspaceStatus.CREATED: {WorkspaceStatus.ACTIVE, WorkspaceStatus.DESTROYED},
    WorkspaceStatus.ACTIVE: {WorkspaceStatus.LOCKED, WorkspaceStatus.ARCHIVED, WorkspaceStatus.DESTROYED},
    WorkspaceStatus.LOCKED: {WorkspaceStatus.ACTIVE, WorkspaceStatus.ARCHIVED, WorkspaceStatus.DESTROYED},
    WorkspaceStatus.ARCHIVED: {WorkspaceStatus.ACTIVE, WorkspaceStatus.DESTROYED},
    WorkspaceStatus.DESTROYED: set(),
}


@dataclass
class Workspace:
    id: str
    name: str
    workspace_type: WorkspaceType
    owner_id: str
    status: WorkspaceStatus = WorkspaceStatus.CREATED
    task_id: str | None = None
    project_id: str | None = None
    employee_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise WorkspaceValidationError("Workspace ID cannot be empty.")
        if not self.name or not self.name.strip():
            raise WorkspaceValidationError("Workspace name cannot be empty.")
        if not self.owner_id or not self.owner_id.strip():
            raise WorkspaceValidationError("Workspace owner_id cannot be empty.")

    def transition_to(self, target_status: WorkspaceStatus) -> None:
        """Execute a deterministic state transition."""
        allowed = VALID_WORKSPACE_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise WorkspaceStateError(
                f"Invalid workspace transition from {self.status.value} to {target_status.value}."
            )

        self.status = target_status
        self.updated_at = datetime.now(UTC)
