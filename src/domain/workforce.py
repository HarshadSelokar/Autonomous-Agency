"""
Workforce Domain Module.

Defines entities, value objects, and enums for capability-based workforce demand,
capacity tracking, capability gap analysis, staffing recommendations, workforce plans,
workforce change requests, workforce decisions, and employee templates.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


from typing import Any


class CapabilityType(str, Enum):
    SOFTWARE_DEVELOPMENT = "SOFTWARE_DEVELOPMENT"
    FRONTEND_DEVELOPMENT = "FRONTEND_DEVELOPMENT"
    BACKEND_DEVELOPMENT = "BACKEND_DEVELOPMENT"
    QA = "QA"
    DEVOPS = "DEVOPS"
    RESEARCH = "RESEARCH"
    MARKETING = "MARKETING"
    SALES = "SALES"
    FINANCE = "FINANCE"
    LEGAL = "LEGAL"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    PROJECT_MANAGEMENT = "PROJECT_MANAGEMENT"
    SECURITY = "SECURITY"
    DATA_ANALYSIS = "DATA_ANALYSIS"


class GapSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StaffingPlanStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"


class WorkforceChangeRequestType(str, Enum):
    CREATE_TEAM = "CREATE_TEAM"
    FORM_TEAM = "FORM_TEAM"
    REALLOCATE_EMPLOYEE = "REALLOCATE_EMPLOYEE"
    CHANGE_ALLOCATION = "CHANGE_ALLOCATION"
    REQUEST_NEW_CAPABILITY = "REQUEST_NEW_CAPABILITY"
    REQUEST_NEW_EMPLOYEE = "REQUEST_NEW_EMPLOYEE"
    DISSOLVE_TEAM = "DISSOLVE_TEAM"


class WorkforceChangeRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class WorkforceHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    BALANCED = "BALANCED"
    AT_RISK = "AT_RISK"
    CAPACITY_CONSTRAINED = "CAPACITY_CONSTRAINED"
    CAPABILITY_CONSTRAINED = "CAPABILITY_CONSTRAINED"
    OVERLOADED = "OVERLOADED"
    PAUSED = "PAUSED"


@dataclass
class WorkforceDemand:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = ""  # e.g., OBJECTIVE, PROJECT, TASK_GRAPH, DEPARTMENT_REQUEST, RECURRING
    source_id: str = ""
    department_id: str | None = None
    capability: str = ""  # CapabilityType or string
    required_count: int = 1
    priority: int = 1  # 1 = low, 5 = critical
    duration_days: int = 30
    deadline: datetime | None = None
    risk_level: str = "LOW"
    governance_required: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.required_count < 1:
            raise ValueError("required_count must be at least 1")


@dataclass
class CapabilityRequirement:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    demand_id: str = ""
    capability: str = ""
    proficiency_level: float = 1.0  # 0.0 to 1.0
    minimum_count: int = 1
    priority: int = 1
    risk_level: str = "LOW"


@dataclass
class CapacitySnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str = ""
    capability: str = ""
    max_capacity: float = 1.0  # 1.0 = 100% capacity
    allocated_capacity: float = 0.0
    available_capacity: float = 1.0
    active_assignments_count: int = 0
    snapshot_time: datetime = field(default_factory=lambda: datetime.now(UTC))

    def calculate_available(self) -> float:
        self.available_capacity = max(0.0, self.max_capacity - self.allocated_capacity)
        return self.available_capacity


@dataclass
class CapabilityGap:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capability: str = ""
    required_count: int = 0
    available_count: int = 0
    gap_count: int = 0
    severity: GapSeverity = GapSeverity.LOW
    affected_project_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StaffingRecommendation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    demand_id: str = ""
    candidate_employee_ids: list[str] = field(default_factory=list)
    capability_fit_score: float = 0.0
    availability_score: float = 0.0
    workload_score: float = 0.0
    reliability_score: float = 0.0
    context_score: float = 0.0
    penalty_score: float = 0.0
    final_score: float = 0.0
    reasoning: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkforceAllocation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str = ""
    team_id: str | None = None
    project_id: str | None = None
    department_id: str | None = None
    allocation_percentage: float = 100.0
    is_temporary: bool = True
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    status: str = "ACTIVE"


@dataclass
class WorkforceChangeRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_type: WorkforceChangeRequestType = WorkforceChangeRequestType.FORM_TEAM
    target_id: str = ""
    requested_by_id: str = ""
    justification: str = ""
    governance_approval_id: str | None = None
    status: WorkforceChangeRequestStatus = WorkforceChangeRequestStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None


@dataclass
class WorkforceDecision:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_request_id: str | None = None
    recommendation_id: str | None = None
    actor_id: str = ""
    manager_id: str | None = None
    human_approver_id: str | None = None
    decision_type: str = "APPROVED"
    reason: str = ""
    policy_applied: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EmployeeTemplate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    role: str = ""
    capabilities: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    default_permissions: list[str] = field(default_factory=list)
    department_compatibility: list[str] = field(default_factory=list)
    governance_requirements: list[str] = field(default_factory=list)
    default_agent_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkforcePlan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    planning_horizon: str = "Q1"
    objectives: list[str] = field(default_factory=list)
    demand_ids: list[str] = field(default_factory=list)
    capacity_snapshot_ids: list[str] = field(default_factory=list)
    gap_ids: list[str] = field(default_factory=list)
    recommendation_ids: list[str] = field(default_factory=list)
    status: StaffingPlanStatus = StaffingPlanStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    approved_at: datetime | None = None
