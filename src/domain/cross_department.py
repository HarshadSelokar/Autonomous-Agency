"""Cross-Department Request, Handoff, Contract, Metrics, and Health Domain Entities for Phase 14."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import List, Optional

from src.domain.department import DepartmentHealth, DepartmentPriority


class DepartmentRequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    REVIEWING = "REVIEWING"
    ACCEPTED = "ACCEPTED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class HandoffStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    VERIFIED = "VERIFIED"


@dataclass
class DepartmentRequest:
    """Formal cross-department work request between requester and delivery owner."""
    request_id: str
    requester_department_id: str
    receiving_department_id: str
    requester_employee_id: str
    receiving_manager_id: str                          # Accountable Manager
    purpose: str
    requested_outcome: str
    delivery_owner_employee_id: Optional[str] = None   # Delivery Owner assigned by manager
    priority: DepartmentPriority = DepartmentPriority.MEDIUM
    sla_deadline: Optional[datetime] = None
    required_capabilities: List[str] = field(default_factory=list)
    status: DepartmentRequestStatus = DepartmentRequestStatus.REQUESTED
    rejection_reason: Optional[str] = None
    related_objective_id: Optional[str] = None
    related_project_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentHandoff:
    """Formal deliverable handoff package between departments backed by evidence."""
    handoff_id: str
    request_id: str
    sender_department_id: str
    receiver_department_id: str
    sender_employee_id: str
    expected_outcome: str
    artifact_ids: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    status: HandoffStatus = HandoffStatus.PROPOSED
    acceptance_criteria: List[str] = field(default_factory=list)
    verification_id: Optional[str] = None
    is_verified: bool = False
    rejection_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentServiceContract:
    """Defined service agreement contract between provider and consumer departments."""
    contract_id: str
    provider_department_id: str
    consumer_department_id: str
    service_name: str
    input_schema_description: str
    expected_output_description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    target_sla_seconds: int = 86400
    required_approvals: List[str] = field(default_factory=list)


@dataclass
class DepartmentMetrics:
    """Quantitative operational metrics for a department derived from Task Engine data."""
    department_id: str
    active_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    incoming_requests: int = 0
    outgoing_requests: int = 0
    verification_success_rate: float = 1.0
    recovery_rate: float = 0.0
    escalation_rate: float = 0.0
    average_completion_time_seconds: float = 0.0


@dataclass
class DepartmentHealthReport:
    """Evaluated health status and bottleneck report for a department."""
    department_id: str
    health: DepartmentHealth
    reason: str
    downstream_blocked_count: int = 0
    metrics: DepartmentMetrics = field(default_factory=lambda: DepartmentMetrics(department_id=""))
    reported_at: datetime = field(default_factory=lambda: datetime.now(UTC))
