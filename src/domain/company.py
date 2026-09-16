"""
Autonomous Company Domain Module.

Defines entities, value objects, and enums for Autonomous Company operations,
operating cycles, metric snapshots, health snapshots, risks, opportunities,
portfolio management, resource plans, and continuous improvement proposals.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid


class CompanyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class OperatingCycleState(str, Enum):
    CREATED = "CREATED"
    OBSERVING = "OBSERVING"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    PRIORITIZING = "PRIORITIZING"
    AWAITING_GOVERNANCE = "AWAITING_GOVERNANCE"
    EXECUTING = "EXECUTING"
    MEASURING = "MEASURING"
    LEARNING = "LEARNING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
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
    scope: str = "COMPANY"  # COMPANY, DEPARTMENT, PROJECT
    scope_id: str | None = None
    trend: MetricTrend = MetricTrend.STABLE
    confidence: float = 1.0  # 0.0 to 1.0
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
    category: str = "OPERATIONAL"  # OPERATIONAL, CAPACITY, RELIABILITY, GOVERNANCE, SECURITY
    probability: float = 0.0  # 0.0 to 1.0
    impact: float = 0.0  # 0.0 to 1.0
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
    item_type: str = "PROJECT"  # INITIATIVE, PROJECT, OBJECTIVE
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
    category: str = "PROCESS"  # PROCESS, TOOLING, RECOVERY, WORKFORCE
    source_event_ids: list[str] = field(default_factory=list)
    proposed_change: str = ""
    expected_impact: str = ""
    governance_required: bool = True
    status: str = "PROPOSED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
