"""
Organizational Experiments Domain Module for Phase 18.

Defines entities, value objects, and enums for governed, isolated organizational experiments.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid


class ExperimentStatus(str, Enum):
    PROPOSED = "PROPOSED"
    AWAITING_GOVERNANCE = "AWAITING_GOVERNANCE"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class OrganizationalExperiment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    hypothesis: str = ""
    objective_id: str | None = None
    scope: str = "COMPANY"
    scope_id: str | None = None
    baseline_metrics: dict[str, Any] = field(default_factory=dict)
    treatment_params: dict[str, Any] = field(default_factory=dict)
    success_criteria: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    duration_hours: int = 24
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    results: dict[str, Any] = field(default_factory=dict)
    conclusion: str = ""
    is_isolated: bool = True
    governance_approval_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.is_isolated:
            object.__setattr__(self, "is_isolated", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "is_isolated" and not value:
            object.__setattr__(self, "is_isolated", True)
            return
        object.__setattr__(self, name, value)
