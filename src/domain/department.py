"""Department Domain Entity and Value Objects for Phase 14.

Implements generic Department framework, cross-department requests, handoffs,
service contracts, metrics, and lifecycle management on Company OS.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class DepartmentStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class DepartmentCapability(str, Enum):
    SOFTWARE_DEVELOPMENT = "SOFTWARE_DEVELOPMENT"
    CODE_REVIEW = "CODE_REVIEW"
    ARCHITECTURE = "ARCHITECTURE"
    TESTING = "TESTING"
    MARKETING_RESEARCH = "MARKETING_RESEARCH"
    CONTENT_CREATION = "CONTENT_CREATION"
    CAMPAIGN_PLANNING = "CAMPAIGN_PLANNING"
    LEAD_QUALIFICATION = "LEAD_QUALIFICATION"
    PROPOSAL_GENERATION = "PROPOSAL_GENERATION"
    FINANCIAL_ANALYSIS = "FINANCIAL_ANALYSIS"
    BUDGETING = "BUDGETING"
    CONTRACT_REVIEW = "CONTRACT_REVIEW"
    COMPLIANCE_ANALYSIS = "COMPLIANCE_ANALYSIS"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    HR_MANAGEMENT = "HR_MANAGEMENT"
    OPERATIONS_PLANNING = "OPERATIONS_PLANNING"


class DepartmentRequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    REVIEWING = "REVIEWING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DELIVERED = "DELIVERED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


class DepartmentRequestPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DepartmentHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    AT_RISK = "AT_RISK"
    PAUSED = "PAUSED"


@dataclass
class Department:
    """Represents an organizational department boundary on Company OS."""
    id: str
    name: str
    code: str
    description: str = ""
    purpose: str = ""
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    responsibilities: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    manager_employee_id: Optional[str] = None
    parent_department_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentRequest:
    """Formal cross-department work request between requester and receiving departments."""
    request_id: str
    requester_department_id: str
    receiving_department_id: str
    requester_employee_id: str
    purpose: str
    requested_outcome: str
    priority: DepartmentRequestPriority = DepartmentRequestPriority.MEDIUM
    status: DepartmentRequestStatus = DepartmentRequestStatus.REQUESTED
    accountable_manager_id: Optional[str] = None
    delivery_owner_employee_id: Optional[str] = None
    target_completion_at: Optional[datetime] = None
    required_capabilities: List[str] = field(default_factory=list)
    related_objective_id: Optional[str] = None
    related_project_id: Optional[str] = None
    governance_request_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentHandoff:
    """Structured deliverable handoff between departments requiring evidence and verification."""
    handoff_id: str
    request_id: str
    sender_department_id: str
    receiving_department_id: str
    sender_employee_id: str
    expected_outcome: str
    receiver_employee_id: Optional[str] = None
    artifact_ids: List[str] = field(default_factory=list)
    evidence_summary: str = ""
    status: str = "PENDING_VERIFICATION"
    verification_id: Optional[str] = None
    accepted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentServiceContract:
    """Formal contract defining service inputs, outputs, SLAs, and rules between departments."""
    contract_id: str
    provider_department_id: str
    consumer_department_id: str
    service_type: str
    required_input_schema: Dict[str, Any] = field(default_factory=dict)
    expected_output_schema: Dict[str, Any] = field(default_factory=dict)
    acceptance_criteria: List[str] = field(default_factory=list)
    sla_seconds: int = 86400
    requires_governance_approval: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DepartmentMetrics:
    """Calculated deterministic metrics and health indicators for a department."""
    department_id: str
    active_task_count: int = 0
    completed_task_count: int = 0
    blocked_task_count: int = 0
    incoming_request_count: int = 0
    outgoing_request_count: int = 0
    verification_failure_count: int = 0
    recovery_attempt_count: int = 0
    escalation_count: int = 0
    health: DepartmentHealth = DepartmentHealth.HEALTHY
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
