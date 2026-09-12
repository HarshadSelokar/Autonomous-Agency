"""
Plan Domain Entity for Organizational Objectives.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import PlanValidationError
from src.domain.work_item import WorkItem


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    REPLANNING = "REPLANNING"
    COMPLETED = "COMPLETED"


@dataclass
class Plan:
    id: str
    objective_id: str
    manager_id: str
    assumptions: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    work_items: list[WorkItem] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id:
            raise PlanValidationError("Plan ID cannot be empty.")
        if not self.objective_id:
            raise PlanValidationError("Plan objective_id cannot be empty.")
        if not self.manager_id:
            raise PlanValidationError("Plan manager_id cannot be empty.")
