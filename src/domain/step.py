"""
ExecutionStep Domain Entity and Value Objects.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class StepType(str, Enum):
    INITIALIZE = "initialize"
    BUILD_CONTEXT = "build_context"
    MODEL_CALL = "model_call"
    VALIDATE_RESPONSE = "validate_response"
    FINALIZE = "finalize"


class StepStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    id: str
    run_id: str
    step_number: int
    step_type: StepType
    status: StepStatus = StepStatus.STARTED
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_completed(self, output_data: dict[str, Any] | None = None) -> None:
        """Mark step as completed successfully."""
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        if output_data is not None:
            self.output_data = output_data

    def mark_failed(self, error_message: str) -> None:
        """Mark step as failed with an error message."""
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.error_message = error_message
