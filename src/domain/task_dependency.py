"""
TaskDependency Domain Entity for Task & Dependency Engine.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import TaskDependencyError


class DependencyType(str, Enum):
    BLOCKING = "BLOCKING"


class DependencyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SATISFIED = "SATISFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class TaskDependency:
    id: str
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType = DependencyType.BLOCKING
    status: DependencyStatus = DependencyStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise TaskDependencyError("TaskDependency ID cannot be empty.")
        if not self.predecessor_task_id:
            raise TaskDependencyError("predecessor_task_id cannot be empty.")
        if not self.successor_task_id:
            raise TaskDependencyError("successor_task_id cannot be empty.")
        if self.predecessor_task_id == self.successor_task_id:
            raise TaskDependencyError(f"Task '{self.predecessor_task_id}' cannot depend on itself.")
