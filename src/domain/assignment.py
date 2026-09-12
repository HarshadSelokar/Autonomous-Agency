"""
Assignment Domain Entity for Employee Work Item Allocation.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import AssignmentError


class AssignmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REASSIGNED = "REASSIGNED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class Assignment:
    id: str
    work_item_id: str
    employee_id: str
    assigned_by: str
    reason: str = ""
    status: AssignmentStatus = AssignmentStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise AssignmentError("Assignment ID cannot be empty.")
        if not self.work_item_id:
            raise AssignmentError("Assignment work_item_id cannot be empty.")
        if not self.employee_id:
            raise AssignmentError("Assignment employee_id cannot be empty.")
        if not self.assigned_by:
            raise AssignmentError("Assignment assigned_by (manager_id) cannot be empty.")
