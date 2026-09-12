"""
WorkItem Domain Entity for Organizational Plan Decomposition.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class WorkItemStatus(str, Enum):
    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


@dataclass
class WorkItem:
    id: str
    plan_id: str
    title: str
    description: str
    required_capabilities: list[str] = field(default_factory=list)
    priority: str = "medium"
    assigned_employee_id: str | None = None
    status: WorkItemStatus = WorkItemStatus.PLANNED
    result: dict[str, Any] | None = None
    blocker_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise ObjectiveValidationError("WorkItem ID cannot be empty.")
        if not self.plan_id:
            raise ObjectiveValidationError("WorkItem plan_id cannot be empty.")
        if not self.title:
            raise ObjectiveValidationError("WorkItem title cannot be empty.")
        if not self.description:
            raise ObjectiveValidationError("WorkItem description cannot be empty.")
