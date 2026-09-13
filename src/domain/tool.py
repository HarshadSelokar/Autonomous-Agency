"""
Tool Domain Entities, Capabilities, Permissions, and Execution State Machines for Phase 8.
Enforces that LLM outputs do NOT directly execute tools without backend validation, authorization, and policy enforcement.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class ToolCategory(str, Enum):
    FILESYSTEM = "FILESYSTEM"
    ARTIFACT = "ARTIFACT"
    TASK = "TASK"
    COMMUNICATION = "COMMUNICATION"
    HTTP = "HTTP"
    BROWSER = "BROWSER"
    DATABASE = "DATABASE"
    GIT = "GIT"
    INTEGRATION = "INTEGRATION"


class ToolCapability(str, Enum):
    READ_FILE = "READ_FILE"
    WRITE_FILE = "WRITE_FILE"
    DELETE_FILE = "DELETE_FILE"
    READ_ARTIFACT = "READ_ARTIFACT"
    CREATE_ARTIFACT = "CREATE_ARTIFACT"
    UPDATE_ARTIFACT = "UPDATE_ARTIFACT"
    HTTP_REQUEST = "HTTP_REQUEST"
    BROWSER_NAVIGATION = "BROWSER_NAVIGATION"
    DATABASE_READ = "DATABASE_READ"
    DATABASE_WRITE = "DATABASE_WRITE"
    GIT_READ = "GIT_READ"
    GIT_WRITE = "GIT_WRITE"
    SEND_MESSAGE = "SEND_MESSAGE"
    CREATE_TASK = "CREATE_TASK"
    READ_TASK = "READ_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    REPORT_PROGRESS = "REPORT_PROGRESS"
    REPORT_BLOCKER = "REPORT_BLOCKER"


class ToolRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PermissionMode(str, Enum):
    AUTO = "AUTO"
    APPROVAL = "APPROVAL"
    BLOCKED = "BLOCKED"


class ToolStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


class ToolExecutionStatus(str, Enum):
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    DENIED = "DENIED"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ToolValidationError(ObjectiveValidationError):
    """Raised when tool domain invariants or validation rules fail."""

    pass


class ToolStateError(ToolValidationError):
    """Raised when an invalid tool execution state transition is attempted."""

    pass


VALID_EXECUTION_TRANSITIONS: dict[ToolExecutionStatus, set[ToolExecutionStatus]] = {
    ToolExecutionStatus.REQUESTED: {ToolExecutionStatus.VALIDATING, ToolExecutionStatus.CANCELLED},
    ToolExecutionStatus.VALIDATING: {
        ToolExecutionStatus.PENDING_APPROVAL,
        ToolExecutionStatus.APPROVED,
        ToolExecutionStatus.DENIED,
        ToolExecutionStatus.CANCELLED,
    },
    ToolExecutionStatus.PENDING_APPROVAL: {
        ToolExecutionStatus.APPROVED,
        ToolExecutionStatus.DENIED,
        ToolExecutionStatus.CANCELLED,
    },
    ToolExecutionStatus.APPROVED: {ToolExecutionStatus.EXECUTING, ToolExecutionStatus.CANCELLED},
    ToolExecutionStatus.EXECUTING: {
        ToolExecutionStatus.SUCCEEDED,
        ToolExecutionStatus.FAILED,
        ToolExecutionStatus.TIMED_OUT,
        ToolExecutionStatus.CANCELLED,
    },
    ToolExecutionStatus.SUCCEEDED: set(),
    ToolExecutionStatus.FAILED: set(),
    ToolExecutionStatus.TIMED_OUT: set(),
    ToolExecutionStatus.CANCELLED: set(),
    ToolExecutionStatus.DENIED: set(),
}


@dataclass
class ToolDefinition:
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: ToolCategory = ToolCategory.INTEGRATION
    capabilities: list[ToolCapability] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    permission_mode: PermissionMode = PermissionMode.AUTO
    provider_name: str = "internal"
    status: ToolStatus = ToolStatus.ACTIVE
    timeout_seconds: float = 30.0
    retry_limit: int = 3
    is_idempotent: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ToolValidationError("Tool ID cannot be empty.")
        if not self.name or not self.name.strip():
            raise ToolValidationError("Tool name cannot be empty.")
        if not self.capabilities:
            raise ToolValidationError(f"Tool '{self.id}' must declare at least one capability.")

    def supports_capability(self, capability: ToolCapability) -> bool:
        return capability in self.capabilities


@dataclass
class ToolRequest:
    id: str
    tool_id: str
    tool_version: str
    requested_capability: ToolCapability
    arguments: dict[str, Any]
    employee_id: str
    agent_id: str
    agent_run_id: str
    task_id: str | None = None
    workspace_id: str | None = None
    purpose: str = ""
    idempotency_key: str | None = None
    correlation_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ToolValidationError("ToolRequest ID cannot be empty.")
        if not self.tool_id or not self.tool_id.strip():
            raise ToolValidationError("ToolRequest tool_id cannot be empty.")
        if not self.employee_id or not self.employee_id.strip():
            raise ToolValidationError("ToolRequest employee_id cannot be empty.")
        if not self.agent_id or not self.agent_id.strip():
            raise ToolValidationError("ToolRequest agent_id cannot be empty.")
        if not self.agent_run_id or not self.agent_run_id.strip():
            raise ToolValidationError("ToolRequest agent_run_id cannot be empty.")


@dataclass
class ToolExecution:
    id: str
    request_id: str
    tool_id: str
    tool_version: str
    capability: ToolCapability
    actor_employee_id: str
    agent_id: str
    agent_run_id: str
    status: ToolExecutionStatus = ToolExecutionStatus.REQUESTED
    task_id: str | None = None
    workspace_id: str | None = None
    approval_id: str | None = None
    failure_reason: str | None = None
    execution_time_ms: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_to(self, target_status: ToolExecutionStatus, failure_reason: str | None = None) -> None:
        allowed = VALID_EXECUTION_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise ToolStateError(
                f"Invalid tool execution transition from {self.status.value} to {target_status.value}."
            )

        self.status = target_status
        if failure_reason:
            self.failure_reason = failure_reason
        self.updated_at = datetime.now(UTC)


@dataclass
class ToolResult:
    execution_id: str
    status: ToolExecutionStatus
    output: dict[str, Any] = field(default_factory=dict)
    output_reference: str | None = None
    error_message: str | None = None
    execution_time_ms: float = 0.0
    evidence_id: str | None = None


@dataclass
class ToolEvidence:
    id: str
    execution_id: str
    tool_id: str
    capability: ToolCapability
    actor_employee_id: str
    agent_id: str
    agent_run_id: str
    status: ToolExecutionStatus
    task_id: str | None = None
    workspace_id: str | None = None
    approval_id: str | None = None
    artifact_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ToolApproval:
    id: str
    execution_id: str
    tool_id: str
    capability: ToolCapability
    requester_employee_id: str
    approver_employee_id: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    rationale: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    approved_at: datetime | None = None

    def approve(self, approver_employee_id: str, rationale: str | None = None) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ToolValidationError(f"Cannot approve tool approval {self.id} in status '{self.status.value}'.")
        self.approver_employee_id = approver_employee_id
        self.status = ApprovalStatus.APPROVED
        self.rationale = rationale
        self.approved_at = datetime.now(UTC)

    def reject(self, approver_employee_id: str, rationale: str | None = None) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ToolValidationError(f"Cannot reject tool approval {self.id} in status '{self.status.value}'.")
        self.approver_employee_id = approver_employee_id
        self.status = ApprovalStatus.REJECTED
        self.rationale = rationale
        self.approved_at = datetime.now(UTC)
