"""
Continuous Organizational Learning & Governed Adaptation Domain Models for Phase 27.

Defines LearningCycle, LearningObservation, ExpectedVsActualComparison, LearningCandidate,
LearningValidation, LearningConflict, LearningPattern, ImprovementOpportunity, AdaptationProposal,
AdaptationEvaluation, AdaptationExecution, AdaptationOutcome, AdaptationImpactAssessment, and LearningReport.

Enforces Fundamental Invariants:
    OBSERVATION != LESSON != KNOWLEDGE != RULE
    PATTERN != CAUSALITY != TRUTH
    CORRELATION != CAUSATION
    LEARNING CANDIDATE != VALIDATED LEARNING != AUTHORITATIVE POLICY
    RECOMMENDATION != ADAPTATION
    ADAPTATION PROPOSAL != APPROVED CHANGE != EXECUTION != SUCCESS
    EXPERIMENT != PRODUCTION CHANGE
    LEARNING != SELF-MODIFICATION
    LEARNING != AUTHORITY
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.company import ExecutionEnvironment
from src.domain.exceptions import (
    InvalidLearningCycleStateError,
    InvalidAdaptationStateError,
    UnauthorizedAdaptationExecutionError,
)


class LearningCycleStatus(str, Enum):
    CREATED = "CREATED"
    COLLECTING = "COLLECTING"
    ANALYZING = "ANALYZING"
    PATTERN_DETECTION = "PATTERN_DETECTION"
    LESSON_GENERATION = "LESSON_GENERATION"
    VALIDATING = "VALIDATING"
    OPPORTUNITY_IDENTIFICATION = "OPPORTUNITY_IDENTIFICATION"
    PROPOSING = "PROPOSING"
    GOVERNANCE_REVIEW = "GOVERNANCE_REVIEW"
    EXPERIMENTING = "EXPERIMENTING"
    MEASURING = "MEASURING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AdaptationType(str, Enum):
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    PROCESS_CHANGE = "PROCESS_CHANGE"
    ROUTING_CHANGE = "ROUTING_CHANGE"
    WORKFLOW_CHANGE = "WORKFLOW_CHANGE"
    TOOL_CONFIGURATION_CHANGE = "TOOL_CONFIGURATION_CHANGE"
    VERIFICATION_RULE_CHANGE = "VERIFICATION_RULE_CHANGE"
    RECOVERY_STRATEGY_CHANGE = "RECOVERY_STRATEGY_CHANGE"
    WORKFORCE_PLANNING_CHANGE = "WORKFORCE_PLANNING_CHANGE"
    KNOWLEDGE_UPDATE = "KNOWLEDGE_UPDATE"
    PRODUCT_PROCESS_CHANGE = "PRODUCT_PROCESS_CHANGE"
    CUSTOMER_PROCESS_CHANGE = "CUSTOMER_PROCESS_CHANGE"
    RESEARCH_PROCESS_CHANGE = "RESEARCH_PROCESS_CHANGE"


class AdaptationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ANALYZING = "ANALYZING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPERIMENTING = "EXPERIMENTING"
    EVALUATING = "EVALUATING"
    ADOPTED = "ADOPTED"
    ROLLED_BACK = "ROLLED_BACK"
    SUPERSEDED = "SUPERSEDED"
    CANCELLED = "CANCELLED"


class LearningScope(str, Enum):
    RUN = "RUN"
    TASK = "TASK"
    PROJECT = "PROJECT"
    TEAM = "TEAM"
    DEPARTMENT = "DEPARTMENT"
    COMPANY = "COMPANY"
    PLATFORM = "PLATFORM"


class AdaptationRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class LearningCycle:
    """Represents an analytical container executing an end-to-end organizational learning iteration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    purpose: str = ""
    scope: LearningScope = LearningScope.COMPANY
    environment: ExecutionEnvironment = ExecutionEnvironment.PRODUCTION
    simulation_id: Optional[str] = None
    status: LearningCycleStatus = LearningCycleStatus.CREATED
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    observations_count: int = 0
    patterns_count: int = 0
    candidates_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_status(self, target_status: LearningCycleStatus) -> None:
        """Enforces valid state machine transitions for learning cycles."""
        valid_transitions = {
            LearningCycleStatus.CREATED: [LearningCycleStatus.COLLECTING, LearningCycleStatus.CANCELLED],
            LearningCycleStatus.COLLECTING: [LearningCycleStatus.ANALYZING, LearningCycleStatus.FAILED],
            LearningCycleStatus.ANALYZING: [LearningCycleStatus.PATTERN_DETECTION, LearningCycleStatus.FAILED],
            LearningCycleStatus.PATTERN_DETECTION: [LearningCycleStatus.LESSON_GENERATION, LearningCycleStatus.FAILED],
            LearningCycleStatus.LESSON_GENERATION: [LearningCycleStatus.VALIDATING, LearningCycleStatus.FAILED],
            LearningCycleStatus.VALIDATING: [LearningCycleStatus.OPPORTUNITY_IDENTIFICATION, LearningCycleStatus.FAILED],
            LearningCycleStatus.OPPORTUNITY_IDENTIFICATION: [LearningCycleStatus.PROPOSING, LearningCycleStatus.COMPLETED, LearningCycleStatus.FAILED],
            LearningCycleStatus.PROPOSING: [LearningCycleStatus.GOVERNANCE_REVIEW, LearningCycleStatus.CANCELLED],
            LearningCycleStatus.GOVERNANCE_REVIEW: [LearningCycleStatus.EXPERIMENTING, LearningCycleStatus.COMPLETED, LearningCycleStatus.CANCELLED],
            LearningCycleStatus.EXPERIMENTING: [LearningCycleStatus.MEASURING, LearningCycleStatus.FAILED],
            LearningCycleStatus.MEASURING: [LearningCycleStatus.COMPLETED, LearningCycleStatus.FAILED],
            LearningCycleStatus.COMPLETED: [],
            LearningCycleStatus.FAILED: [],
            LearningCycleStatus.CANCELLED: [],
        }
        allowed = valid_transitions.get(self.status, [])
        if target_status not in allowed:
            raise InvalidLearningCycleStateError(self.id, self.status.value, target_status.value)
        self.status = target_status
        self.updated_at = datetime.now(UTC)


@dataclass
class LearningObservation:
    """Structured observation record captured from operational subsystem events."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str = ""
    company_id: str = ""
    source_subsystem: str = ""  # e.g., TASK_ENGINE, MODEL_ROUTER, RECOVERY, CRM, DECISION
    entity_reference: str = ""
    observed_value: Any = None
    expected_value: Any = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ExpectedVsActualComparison:
    """Structured variance comparison record evaluating expected vs actual operational metrics."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str = ""
    company_id: str = ""
    domain: str = ""  # e.g., DECISION, FORECAST, TASK_DURATION, MODEL_LATENCY, REVENUE
    metric_name: str = ""
    expected_value: float = 0.0
    actual_value: float = 0.0
    variance: float = 0.0
    variance_percentage: float = 0.0
    confidence: float = 0.90
    context: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LearningCandidate:
    """Hypothesis/candidate lesson statement awaiting formal validation and evidence backing."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str = ""
    company_id: str = ""
    statement: str = ""
    scope: LearningScope = LearningScope.COMPANY
    supporting_observation_ids: List[str] = field(default_factory=list)
    counterexamples: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    confidence: float = 0.50
    generated_by: str = "SYSTEM"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LearningValidation:
    """Formal validation record confirming or rejecting a candidate lesson based on evidence."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    candidate_id: str = ""
    company_id: str = ""
    validation_method: str = "HISTORICAL_ANALYSIS"  # e.g., HISTORICAL_ANALYSIS, EXPERIMENT, REPEATED_OBSERVATION
    is_valid: bool = False
    evidence_score: float = 0.50
    validation_notes: str = ""
    validated_by: str = "SYSTEM"
    validated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LearningConflict:
    """Record tracking contradictory evidence or conflicting lesson claims across different contexts."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    lesson_a_id: str = ""
    lesson_b_id: str = ""
    conflict_summary: str = ""
    context_discrepancies: List[str] = field(default_factory=list)
    status: str = "OPEN"
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LearningPattern:
    """Detected recurring pattern across operational executions (failures, successes, bottlenecks)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    pattern_name: str = ""
    pattern_type: str = "RECURRING_FAILURE"  # e.g., RECURRING_FAILURE, RECURRING_SUCCESS, BOTTLENECK
    frequency: int = 1
    scope: LearningScope = LearningScope.COMPANY
    confidence: float = 0.85
    evidence_references: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ImprovementOpportunity:
    """Identified institutional optimization opportunity derived from validated patterns and lessons."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    affected_area: str = ""
    expected_impact: str = ""
    required_resources: Dict[str, Any] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    confidence: float = 0.80
    identified_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AdaptationProposal:
    """Formal proposal for a controlled organizational configuration, workflow, or routing adaptation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    opportunity_id: str = ""
    adaptation_type: AdaptationType = AdaptationType.WORKFLOW_CHANGE
    risk_level: AdaptationRiskLevel = AdaptationRiskLevel.MEDIUM
    current_state: Dict[str, Any] = field(default_factory=dict)
    proposed_state: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    rollback_plan: Dict[str, Any] = field(default_factory=dict)
    status: AdaptationStatus = AdaptationStatus.PROPOSED
    governance_required: bool = True
    governance_approval_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_status(self, target_status: AdaptationStatus) -> None:
        """Enforces valid state machine transitions for adaptation proposals."""
        valid_transitions = {
            AdaptationStatus.PROPOSED: [AdaptationStatus.ANALYZING, AdaptationStatus.APPROVED, AdaptationStatus.EXPERIMENTING, AdaptationStatus.REJECTED, AdaptationStatus.CANCELLED],
            AdaptationStatus.ANALYZING: [AdaptationStatus.REVIEW_REQUIRED, AdaptationStatus.APPROVED, AdaptationStatus.EXPERIMENTING, AdaptationStatus.REJECTED],
            AdaptationStatus.REVIEW_REQUIRED: [AdaptationStatus.APPROVED, AdaptationStatus.REJECTED, AdaptationStatus.CANCELLED],
            AdaptationStatus.APPROVED: [AdaptationStatus.EXPERIMENTING, AdaptationStatus.ADOPTED, AdaptationStatus.CANCELLED],
            AdaptationStatus.REJECTED: [],
            AdaptationStatus.EXPERIMENTING: [AdaptationStatus.EVALUATING, AdaptationStatus.ROLLED_BACK, AdaptationStatus.FAILED if hasattr(AdaptationStatus, "FAILED") else AdaptationStatus.ROLLED_BACK],
            AdaptationStatus.EVALUATING: [AdaptationStatus.ADOPTED, AdaptationStatus.ROLLED_BACK],
            AdaptationStatus.ADOPTED: [AdaptationStatus.SUPERSEDED, AdaptationStatus.ROLLED_BACK],
            AdaptationStatus.ROLLED_BACK: [],
            AdaptationStatus.SUPERSEDED: [],
            AdaptationStatus.CANCELLED: [],
        }
        allowed = valid_transitions.get(self.status, [])
        if target_status not in allowed:
            raise InvalidAdaptationStateError(self.id, self.status.value, target_status.value)
        self.status = target_status
        self.updated_at = datetime.now(UTC)

    def assert_valid_for_execution(self) -> None:
        """Enforces mandatory human governance approval boundary prior to execution or experiment dispatch."""
        if self.governance_required and not self.governance_approval_id:
            raise UnauthorizedAdaptationExecutionError(
                self.id, "Human governance approval strictly required prior to dispatching adaptation execution."
            )


@dataclass
class AdaptationEvaluation:
    """Multi-dimensional evaluation of an AdaptationProposal (assessing benefit, risk, cost, reversibility)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    expected_benefit_score: float = 0.50
    risk_score: float = 0.50
    cost_score: float = 0.50
    reversibility_score: float = 0.50
    overall_recommendation_score: float = 0.50
    evaluation_breakdown: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AdaptationExecution:
    """Staged execution record for a controlled experiment or adoption dispatch."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    governance_approval_id: str = ""
    execution_type: str = "CONTROLLED_EXPERIMENT"  # CONTROLLED_EXPERIMENT or DIRECT_ADOPTION
    target_subsystem: str = ""
    execution_payload: Dict[str, Any] = field(default_factory=dict)
    dispatched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None


@dataclass
class AdaptationOutcome:
    """Post-adaptation measurement evaluating direct outcomes, side effects, and regressions."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = ""
    proposal_id: str = ""
    company_id: str = ""
    expected_metrics: Dict[str, Any] = field(default_factory=dict)
    actual_metrics: Dict[str, Any] = field(default_factory=dict)
    variance_analysis: Dict[str, Any] = field(default_factory=dict)
    side_effects_detected: List[str] = field(default_factory=list)
    has_regression: bool = False
    measured_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AdaptationImpactAssessment:
    """Assessment of downstream system dependencies, affected teams/tools/models, and rollback feasibility."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    affected_subsystems: List[str] = field(default_factory=list)
    downstream_dependencies: List[str] = field(default_factory=list)
    rollback_feasibility_score: float = 1.00
    assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LearningReport:
    """Complete provenance brief documenting an end-to-end organizational learning cycle."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str = ""
    company_id: str = ""
    observations: List[Dict[str, Any]] = field(default_factory=list)
    variance_records: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    validated_lessons: List[Dict[str, Any]] = field(default_factory=list)
    proposals: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
