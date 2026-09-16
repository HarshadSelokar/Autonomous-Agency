"""
Multi-Company & Multi-Tenant Organization Domain Models for Phase 25 (and Phase 16 Autonomous Company Operations).

Defines first-class Company entity, Lifecycle state machine, Profiles, Memberships,
Templates, Governed Cross-Company Relationships, Data Share Requests, Resource Quotas,
and CompanyContext boundary objects.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.exceptions import (
    InvalidLifecycleTransitionError,
    TenantIsolationViolationError,
)


class CompanyLifecycle(str, Enum):
    PROPOSED = "PROPOSED"
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class CompanyType(str, Enum):
    AUTONOMOUS = "AUTONOMOUS"
    INTERNAL = "INTERNAL"
    SANDBOX = "SANDBOX"
    SIMULATION = "SIMULATION"
    EXPERIMENTAL = "EXPERIMENTAL"


class CompanyRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    MANAGER = "MANAGER"
    VIEWER = "VIEWER"
    AUDITOR = "AUDITOR"


class RelationshipType(str, Enum):
    PARTNER = "PARTNER"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    SUBSIDIARY = "SUBSIDIARY"
    PARENT = "PARENT"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    COLLABORATOR = "COLLABORATOR"
    COMPETITOR = "COMPETITOR"
    INTERNAL = "INTERNAL"
    OTHER = "OTHER"


class DataShareScope(str, Enum):
    READ_ONLY = "READ_ONLY"
    AGGREGATED = "AGGREGATED"
    SPECIFIC_RECORD = "SPECIFIC_RECORD"
    DOCUMENT = "DOCUMENT"
    METRIC = "METRIC"
    API_RESULT = "API_RESULT"


class DataShareStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ExecutionEnvironment(str, Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    SANDBOX = "SANDBOX"
    SIMULATION = "SIMULATION"


# --- Legacy Phase 16 Domain Enums ---

class CompanyStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DEGRADED = "DEGRADED"
    RECOVERY = "RECOVERY"
    MAINTENANCE = "MAINTENANCE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class OperatingCycleState(str, Enum):
    CREATED = "CREATED"
    OBSERVING = "OBSERVING"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    PRIORITIZING = "PRIORITIZING"
    AWAITING_GOVERNANCE = "AWAITING_GOVERNANCE"
    EXECUTING = "EXECUTING"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    MEASURING = "MEASURING"
    LEARNING = "LEARNING"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MetricTrend(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    STABLE = "STABLE"


class CompanyHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    BALANCED = "BALANCED"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ObservationFactType(str, Enum):
    FACT = "FACT"
    OBSERVATION = "OBSERVATION"
    INFERENCE = "INFERENCE"
    PREDICTION = "PREDICTION"
    RECOMMENDATION = "RECOMMENDATION"
    METRIC_UPDATE = "METRIC_UPDATE"
    RISK_SIGNAL = "RISK_SIGNAL"


# --- Legacy Phase 16 Entities ---

@dataclass
class ObservationFact:
    fact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    fact_type: ObservationFactType = ObservationFactType.FACT
    source: str = "system"
    summary: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AutonomousCompany:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Autonomous AI Organization"
    code: str = "AAO"
    mission: str = "Build, verify, and operate software and enterprise systems autonomously."
    status: CompanyStatus = CompanyStatus.ACTIVE
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyOperatingCycle:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    cycle_number: int = 1
    state: OperatingCycleState = OperatingCycleState.CREATED
    checkpoint_data: dict[str, Any] = field(default_factory=dict)
    initiated_by_id: str = "system"
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    failure_reason: str | None = None

    def transition_to(self, target_state: OperatingCycleState, checkpoint_info: dict[str, Any] | None = None) -> None:
        valid_transitions = {
            OperatingCycleState.CREATED: {OperatingCycleState.OBSERVING, OperatingCycleState.PAUSED, OperatingCycleState.CANCELLED},
            OperatingCycleState.OBSERVING: {OperatingCycleState.ANALYZING, OperatingCycleState.FAILED, OperatingCycleState.PAUSED},
            OperatingCycleState.ANALYZING: {OperatingCycleState.PLANNING, OperatingCycleState.FAILED, OperatingCycleState.PAUSED},
            OperatingCycleState.PLANNING: {OperatingCycleState.PRIORITIZING, OperatingCycleState.FAILED, OperatingCycleState.PAUSED},
            OperatingCycleState.PRIORITIZING: {OperatingCycleState.AWAITING_GOVERNANCE, OperatingCycleState.EXECUTING, OperatingCycleState.FAILED},
            OperatingCycleState.AWAITING_GOVERNANCE: {OperatingCycleState.EXECUTING, OperatingCycleState.HUMAN_REVIEW, OperatingCycleState.FAILED, OperatingCycleState.CANCELLED},
            OperatingCycleState.EXECUTING: {OperatingCycleState.MEASURING, OperatingCycleState.RECOVERY_REQUIRED, OperatingCycleState.FAILED},
            OperatingCycleState.RECOVERY_REQUIRED: {OperatingCycleState.EXECUTING, OperatingCycleState.FAILED, OperatingCycleState.HUMAN_REVIEW},
            OperatingCycleState.MEASURING: {OperatingCycleState.LEARNING, OperatingCycleState.FAILED},
            OperatingCycleState.LEARNING: {OperatingCycleState.COMPLETED, OperatingCycleState.FAILED},
            OperatingCycleState.HUMAN_REVIEW: {OperatingCycleState.EXECUTING, OperatingCycleState.PLANNING, OperatingCycleState.CANCELLED},
            OperatingCycleState.PAUSED: {OperatingCycleState.OBSERVING, OperatingCycleState.ANALYZING, OperatingCycleState.PLANNING, OperatingCycleState.EXECUTING, OperatingCycleState.CANCELLED},
            OperatingCycleState.FAILED: {OperatingCycleState.RECOVERY_REQUIRED, OperatingCycleState.HUMAN_REVIEW, OperatingCycleState.CANCELLED},
        }
        allowed = valid_transitions.get(self.state, set())
        if target_state not in allowed and target_state != OperatingCycleState.CANCELLED:
            raise ValueError(f"Invalid operating cycle state transition from {self.state} to {target_state}")

        self.state = target_state
        if checkpoint_info:
            self.checkpoint_data.update(checkpoint_info)
        if target_state == OperatingCycleState.COMPLETED:
            self.completed_at = datetime.now(UTC)


@dataclass
class CompanyKPISnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    metric_name: str = ""
    value: float = 0.0
    target_value: float = 0.0
    scope: str = "COMPANY"
    scope_id: str | None = None
    trend: MetricTrend = MetricTrend.STABLE
    confidence: float = 1.0
    freshness_seconds: int = 0
    provenance_sources: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyHealthSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    operational_health: float = 1.0
    execution_health: float = 1.0
    delivery_health: float = 1.0
    quality_health: float = 1.0
    workforce_health: float = 1.0
    reliability_health: float = 1.0
    resource_health: float = 1.0
    governance_health: float = 1.0
    security_health: float = 1.0
    overall_status: CompanyHealthStatus = CompanyHealthStatus.HEALTHY
    explanation: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyRisk:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    category: str = "OPERATIONAL"
    probability: float = 0.0
    impact: float = 0.0
    severity: RiskSeverity = RiskSeverity.LOW
    evidence_ids: list[str] = field(default_factory=list)
    affected_entity_ids: list[str] = field(default_factory=list)
    mitigation_plan: str = ""
    status: str = "OPEN"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyOpportunity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    category: str = "EFFICIENCY"
    expected_value: float = 0.0
    required_resources: str = ""
    affected_objective_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0
    status: str = "OPEN"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PortfolioItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    item_type: str = "PROJECT"
    reference_id: str = ""
    priority: int = 1
    progress_pct: float = 0.0
    resource_utilization_pct: float = 0.0
    status: str = "ACTIVE"
    has_bottleneck: bool = False
    bottleneck_description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResourceAllocationPlan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    cycle_id: str | None = None
    demand_summary: str = ""
    allocations_json: dict[str, Any] = field(default_factory=dict)
    constraints_json: dict[str, Any] = field(default_factory=dict)
    tradeoffs_summary: str = ""
    is_approved: bool = False
    approved_by_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ContinuousImprovementProposal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    category: str = "PROCESS"
    source_event_ids: list[str] = field(default_factory=list)
    proposed_change: str = ""
    expected_impact: str = ""
    governance_required: bool = True
    status: str = "PROPOSED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# --- Phase 25 Multi-Company Entities ---

@dataclass
class Company:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    legal_name: str = ""
    slug: str = ""
    description: str = ""
    company_type: CompanyType = CompanyType.AUTONOMOUS
    industry: str = "TECHNOLOGY"
    timezone: str = "UTC"
    locale: str = "en_US"
    currency: str = "USD"
    lifecycle: CompanyLifecycle = CompanyLifecycle.PROPOSED
    owner_id: str = "SYSTEM"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_lifecycle(self, target_lifecycle: CompanyLifecycle) -> None:
        """Enforces valid company lifecycle transitions."""
        valid_transitions = {
            CompanyLifecycle.PROPOSED: [CompanyLifecycle.INITIALIZING, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.INITIALIZING: [CompanyLifecycle.ACTIVE, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.ACTIVE: [CompanyLifecycle.PAUSED, CompanyLifecycle.SUSPENDED, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.PAUSED: [CompanyLifecycle.ACTIVE, CompanyLifecycle.SUSPENDED, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.SUSPENDED: [CompanyLifecycle.ACTIVE, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.ARCHIVED: [],  # Terminal state
        }

        allowed = valid_transitions.get(self.lifecycle, [])
        if target_lifecycle not in allowed:
            raise InvalidLifecycleTransitionError(self.id, self.lifecycle.value, target_lifecycle.value)

        self.lifecycle = target_lifecycle
        self.updated_at = datetime.now(UTC)


@dataclass
class CompanyProfile:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    operating_hours: str = "24/7"
    model_routing_policy: Dict[str, Any] = field(default_factory=dict)
    tool_policy: Dict[str, Any] = field(default_factory=dict)
    governance_defaults: Dict[str, Any] = field(default_factory=dict)
    workforce_config: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyMembership:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    user_id: str = ""
    role: CompanyRole = CompanyRole.VIEWER
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyTemplate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    industry: str = ""
    structure_json: Dict[str, Any] = field(default_factory=dict)
    default_departments: List[str] = field(default_factory=list)
    default_roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyRelationship:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_a_id: str = ""
    company_b_id: str = ""
    relationship_type: RelationshipType = RelationshipType.PARTNER
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyDataShareRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_company_id: str = ""
    target_company_id: str = ""
    data_scope: DataShareScope = DataShareScope.READ_ONLY
    purpose: str = ""
    status: DataShareStatus = DataShareStatus.REQUESTED
    governance_approval_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None


@dataclass
class CompanyResourceQuota:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    max_concurrent_tasks: int = 100
    max_concurrent_agents: int = 50
    max_monthly_model_calls: int = 100000
    max_storage_mb: int = 50000
    max_simulations: int = 10
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyResourceUsage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    active_tasks: int = 0
    active_agents: int = 0
    monthly_model_calls: int = 0
    storage_mb: int = 0
    active_simulations: int = 0
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class CompanyContext:
    company_id: str
    user_id: str = "SYSTEM"
    role: CompanyRole = CompanyRole.ADMIN
    environment: ExecutionEnvironment = ExecutionEnvironment.PRODUCTION
    simulation_id: Optional[str] = None

    def verify_company_access(self, target_company_id: str, resource_type: str = "resource") -> None:
        """Enforces tenant isolation between company contexts."""
        if self.company_id != target_company_id:
            raise TenantIsolationViolationError(self.company_id, target_company_id, resource_type)
