"""
Recovery Domain Entities and Value Objects for Phase 10.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class FailureCategory(str, Enum):
    AGENT_FAILURE = "AGENT_FAILURE"
    TOOL_FAILURE = "TOOL_FAILURE"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    TEST_FAILURE = "TEST_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    POLICY_FAILURE = "POLICY_FAILURE"
    TIMEOUT = "TIMEOUT"
    RESOURCE_FAILURE = "RESOURCE_FAILURE"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    REQUIREMENT_FAILURE = "REQUIREMENT_FAILURE"
    QUALITY_FAILURE = "QUALITY_FAILURE"
    SECURITY_FAILURE = "SECURITY_FAILURE"
    EXTERNAL_SERVICE_FAILURE = "EXTERNAL_SERVICE_FAILURE"
    APPROVAL_FAILURE = "APPROVAL_FAILURE"
    HUMAN_REVIEW_FAILURE = "HUMAN_REVIEW_FAILURE"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class RecoveryStrategy(str, Enum):
    RETRY = "RETRY"
    REEXECUTE = "REEXECUTE"
    REWORK = "REWORK"
    REASSIGN = "REASSIGN"
    ESCALATE = "ESCALATE"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    ROLLBACK = "ROLLBACK"
    COMPENSATE = "COMPENSATE"
    SUSPEND = "SUSPEND"
    CANCEL = "CANCEL"


@dataclass
class FailureRecord:
    """Represents a recorded execution or verification failure."""
    failure_id: str
    task_id: str
    verification_id: str | None
    category: FailureCategory
    severity: str                         # e.g., "HIGH", "MEDIUM", "CRITICAL"
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = True
    recoverable: bool = True
    recommended_strategy: RecoveryStrategy | None = None
    agent_id: str | None = None
    employee_id: str | None = None
    execution_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FailureBudget:
    """Configurable failure limits for recovery loop protection."""
    max_retries: int = 3
    max_reworks: int = 3
    max_reassignments: int = 2
    max_recovery_attempts: int = 5
    max_execution_duration_seconds: int = 3600

    def is_retry_exhausted(self, retry_count: int) -> bool:
        return retry_count >= self.max_retries

    def is_rework_exhausted(self, rework_count: int) -> bool:
        return rework_count >= self.max_reworks

    def is_reassignment_exhausted(self, reassignment_count: int) -> bool:
        return reassignment_count >= self.max_reassignments


@dataclass
class RecoveryAction:
    """Represents a specific recovery action executed by the RecoveryEngine."""
    action_id: str
    failure_id: str
    task_id: str
    strategy: RecoveryStrategy
    attempt_number: int
    success: bool
    details: dict[str, Any] = field(default_factory=dict)
    executed_by: str = "SYSTEM"           # "SYSTEM" or "MANAGER" or "HUMAN"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
