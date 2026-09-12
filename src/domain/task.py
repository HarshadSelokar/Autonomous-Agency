"""
Task Domain Entity and Lifecycle State Machine for Task Engine.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import InvalidStateTransitionError, TaskValidationError


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    BLOCKED = "BLOCKED"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    REWORK = "REWORK"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BlockReason(str, Enum):
    DEPENDENCY_INCOMPLETE = "DEPENDENCY_INCOMPLETE"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    NO_ELIGIBLE_EMPLOYEE = "NO_ELIGIBLE_EMPLOYEE"
    POLICY_BLOCK = "POLICY_BLOCK"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"


VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.PLANNED, TaskStatus.CANCELLED},
    TaskStatus.PLANNED: {TaskStatus.BLOCKED, TaskStatus.READY, TaskStatus.CANCELLED},
    TaskStatus.BLOCKED: {TaskStatus.READY, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.READY: {TaskStatus.ASSIGNED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.ASSIGNED: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.READY,
        TaskStatus.BLOCKED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.REVIEW: {
        TaskStatus.APPROVED,
        TaskStatus.REWORK,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.REWORK: {TaskStatus.IN_PROGRESS, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.APPROVED: {TaskStatus.COMPLETED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: {
        TaskStatus.READY,
        TaskStatus.PLANNED,
        TaskStatus.REWORK,
        TaskStatus.CANCELLED,
    },
    TaskStatus.CANCELLED: set(),
}


@dataclass
class Task:
    id: str
    plan_id: str
    title: str
    description: str
    objective_id: str | None = None
    work_item_id: str | None = None
    parent_task_id: str | None = None
    required_capabilities: list[str] = field(default_factory=list)
    priority: str = "medium"
    status: TaskStatus = TaskStatus.CREATED
    assigned_employee_id: str | None = None
    assignment_id: str | None = None
    execution_run_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    block_reasons: list[BlockReason] = field(default_factory=list)
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise TaskValidationError("Task ID cannot be empty.")
        if not self.plan_id:
            raise TaskValidationError("Task plan_id cannot be empty.")
        if not self.title:
            raise TaskValidationError("Task title cannot be empty.")
        if not self.description:
            raise TaskValidationError("Task description cannot be empty.")
        if self.priority not in {"low", "medium", "high", "critical"}:
            raise TaskValidationError(
                f"Invalid priority '{self.priority}'. Must be low, medium, high, or critical."
            )
        if self.retry_count < 0:
            raise TaskValidationError("retry_count cannot be negative.")
        if self.max_retries < 0:
            raise TaskValidationError("max_retries cannot be negative.")

    def can_transition_to(self, target_status: TaskStatus) -> bool:
        allowed = VALID_TRANSITIONS.get(self.status, set())
        return target_status in allowed

    def transition_to(self, target_status: TaskStatus, reason: str | None = None) -> None:
        if not self.can_transition_to(target_status):
            raise InvalidStateTransitionError(
                entity="Task",
                entity_id=self.id,
                current_state=self.status.value,
                target_state=target_status.value,
            )
        self.status = target_status
        self.updated_at = datetime.now(UTC)
        if reason and target_status == TaskStatus.BLOCKED:
            if BlockReason(reason) not in self.block_reasons:
                self.block_reasons.append(BlockReason(reason))
        elif target_status != TaskStatus.BLOCKED:
            self.block_reasons.clear()
