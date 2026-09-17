"""
Advanced Company Intelligence & Decision Support Domain Models for Phase 26.

Defines IntelligenceRun, DecisionQuestion, DecisionOption, DecisionEvaluation,
StrategicTradeoff, CompanyHealthAssessment, CompanyBottleneck, CompanyRiskAssessment,
CompanyOpportunityAssessment, DecisionInsight, and DecisionOutcomeEvaluation.

Enforces Fundamental Invariants:
    FACT != OBSERVATION != FORECAST != PREDICTION != SCENARIO != REALITY
    RECOMMENDATION != DECISION
    APPROVED DECISION != EXECUTION != VERIFICATION != OUTCOME != LEARNING
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.company import ExecutionEnvironment
from src.domain.exceptions import (
    CompanyIntelligenceError,
    DecisionInsightExpiredError,
    UnauthorizedDecisionExecutionError,
    InvalidIntelligenceRunStateError,
)


class IntelligenceRunStatus(str, Enum):
    REQUESTED = "REQUESTED"
    QUEUED = "QUEUED"
    COLLECTING_DATA = "COLLECTING_DATA"
    ANALYZING = "ANALYZING"
    MODELING = "MODELING"
    EVALUATING = "EVALUATING"
    GENERATING_INSIGHTS = "GENERATING_INSIGHTS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class QuestionUrgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    STRATEGIC = "STRATEGIC"
    OPERATIONAL = "OPERATIONAL"
    FINANCIAL = "FINANCIAL"
    CUSTOMER = "CUSTOMER"
    PRODUCT = "PRODUCT"
    WORKFORCE = "WORKFORCE"
    TECHNOLOGY = "TECHNOLOGY"
    SECURITY = "SECURITY"
    GOVERNANCE = "GOVERNANCE"
    RELIABILITY = "RELIABILITY"


class HealthDimension(str, Enum):
    STRATEGIC = "STRATEGIC"
    FINANCIAL = "FINANCIAL"
    PRODUCT = "PRODUCT"
    CUSTOMER = "CUSTOMER"
    GTM = "GTM"
    WORKFORCE = "WORKFORCE"
    ENGINEERING = "ENGINEERING"
    OPERATIONS = "OPERATIONS"
    RELIABILITY = "RELIABILITY"
    GOVERNANCE = "GOVERNANCE"


@dataclass
class IntelligenceRun:
    """Represents a deterministic analytical execution run gathering evidence and generating insights."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    purpose: str = ""
    scope: str = "FULL_COMPANY"
    environment: ExecutionEnvironment = ExecutionEnvironment.PRODUCTION
    simulation_id: Optional[str] = None
    status: IntelligenceRunStatus = IntelligenceRunStatus.REQUESTED
    requesting_principal: str = "SYSTEM"
    data_sources: List[str] = field(default_factory=list)
    model_metadata: Dict[str, Any] = field(default_factory=dict)
    findings_count: int = 0
    uncertainty_score: float = 0.1
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_status(self, target_status: IntelligenceRunStatus) -> None:
        """Enforces valid status transitions for intelligence runs."""
        valid_transitions = {
            IntelligenceRunStatus.REQUESTED: [IntelligenceRunStatus.QUEUED, IntelligenceRunStatus.COLLECTING_DATA, IntelligenceRunStatus.CANCELLED],
            IntelligenceRunStatus.QUEUED: [IntelligenceRunStatus.COLLECTING_DATA, IntelligenceRunStatus.CANCELLED],
            IntelligenceRunStatus.COLLECTING_DATA: [IntelligenceRunStatus.ANALYZING, IntelligenceRunStatus.FAILED],
            IntelligenceRunStatus.ANALYZING: [IntelligenceRunStatus.MODELING, IntelligenceRunStatus.FAILED],
            IntelligenceRunStatus.MODELING: [IntelligenceRunStatus.EVALUATING, IntelligenceRunStatus.FAILED],
            IntelligenceRunStatus.EVALUATING: [IntelligenceRunStatus.GENERATING_INSIGHTS, IntelligenceRunStatus.FAILED],
            IntelligenceRunStatus.GENERATING_INSIGHTS: [IntelligenceRunStatus.REVIEW_REQUIRED, IntelligenceRunStatus.COMPLETED, IntelligenceRunStatus.FAILED],
            IntelligenceRunStatus.REVIEW_REQUIRED: [IntelligenceRunStatus.COMPLETED, IntelligenceRunStatus.CANCELLED],
            IntelligenceRunStatus.COMPLETED: [],
            IntelligenceRunStatus.FAILED: [],
            IntelligenceRunStatus.CANCELLED: [],
        }
        allowed = valid_transitions.get(self.status, [])
        if target_status not in allowed:
            raise InvalidIntelligenceRunStateError(self.id, self.status.value, target_status.value)
        self.status = target_status
        self.updated_at = datetime.now(UTC)


@dataclass
class IntelligenceFinding:
    """Individual observation or analytical finding produced during an IntelligenceRun."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    company_id: str = ""
    title: str = ""
    observation_summary: str = ""
    evidence_references: List[str] = field(default_factory=list)
    confidence: float = 0.90
    is_anomaly: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DecisionQuestion:
    """First-class decision query to be analyzed by the decision support engine."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    question: str = ""
    purpose: str = ""
    scope: str = "STRATEGIC"
    urgency: QuestionUrgency = QuestionUrgency.MEDIUM
    requester_id: str = "SYSTEM"
    constraints: List[str] = field(default_factory=list)
    decision_deadline: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DecisionOption:
    """Discrete strategic alternative evaluated for a DecisionQuestion (includes NO_ACTION)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    company_id: str = ""
    option_name: str = ""
    description: str = ""
    is_no_action_baseline: bool = False
    assumptions: List[str] = field(default_factory=list)
    required_resources: Dict[str, Any] = field(default_factory=dict)
    expected_benefits: Dict[str, Any] = field(default_factory=dict)
    expected_costs_cents: int = 0
    risk_factors: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    scenario_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DecisionEvaluation:
    """Multi-dimensional evaluation of a single DecisionOption."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    option_id: str = ""
    company_id: str = ""
    strategic_alignment_score: float = 0.5
    financial_impact_score: float = 0.5
    customer_impact_score: float = 0.5
    product_impact_score: float = 0.5
    workforce_impact_score: float = 0.5
    operational_risk_score: float = 0.5
    execution_complexity_score: float = 0.5
    reversibility_score: float = 0.5
    confidence_score: float = 0.85
    overall_score: float = 0.5
    evaluation_breakdown: Dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StrategicTradeoff:
    """Explicit trade-off comparison between two decision options."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    company_id: str = ""
    option_a_id: str = ""
    option_b_id: str = ""
    tradeoff_summary: str = ""
    option_a_advantages: List[str] = field(default_factory=list)
    option_b_advantages: List[str] = field(default_factory=list)
    opportunity_cost_a_cents: int = 0
    opportunity_cost_b_cents: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyHealthAssessment:
    """Multi-dimensional health evaluation across company operating domains."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    overall_health_status: str = "HEALTHY"
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    key_findings: List[str] = field(default_factory=list)
    top_risks: List[str] = field(default_factory=list)
    top_opportunities: List[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyBottleneck:
    """Detected operational bottleneck affecting company performance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    bottleneck_name: str = ""
    affected_scope: str = ""
    severity: str = "MEDIUM"
    evidence_summary: str = ""
    suspected_causes: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_resolved: bool = False


@dataclass
class CompanyRiskAssessment:
    """Categorized risk assessment item with probability, impact, and mitigations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    category: RiskCategory = RiskCategory.OPERATIONAL
    probability_score: float = 0.3
    impact_score: float = 0.5
    severity: str = "MEDIUM"
    leading_indicators: List[str] = field(default_factory=list)
    mitigation_options: List[str] = field(default_factory=list)
    confidence: float = 0.85
    assessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyOpportunityAssessment:
    """Identified strategic or operational opportunity with potential impact."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    description: str = ""
    potential_impact_cents: int = 0
    required_resources: List[str] = field(default_factory=list)
    confidence: float = 0.80
    research_request_id: Optional[str] = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DecisionInsight:
    """Complete decision intelligence artifact containing options, evaluations, evidence graph, and recommendations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    company_id: str = ""
    version: int = 1
    evidence_graph: Dict[str, Any] = field(default_factory=dict)
    options: List[Dict[str, Any]] = field(default_factory=list)
    tradeoffs: List[Dict[str, Any]] = field(default_factory=list)
    recommendation_summary: str = ""
    recommended_option_id: Optional[str] = None
    uncertainty_analysis: Dict[str, Any] = field(default_factory=dict)
    governance_required: bool = True
    governance_approval_id: Optional[str] = None
    is_executed: bool = False
    is_expired: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def assert_valid_for_execution(self) -> None:
        """Verifies insight is unexpired and approved before triggering execution bridge."""
        if self.is_expired:
            raise DecisionInsightExpiredError(self.id, "Decision insight has expired.")
        if self.governance_required and not self.governance_approval_id:
            raise UnauthorizedDecisionExecutionError(self.id, "Human governance approval strictly required prior to execution.")


@dataclass
class DecisionOutcomeEvaluation:
    """Post-execution feedback record comparing expected vs actual outcomes to enable institutional learning."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insight_id: str = ""
    company_id: str = ""
    executed_option_id: str = ""
    expected_outcomes: Dict[str, Any] = field(default_factory=dict)
    actual_outcomes: Dict[str, Any] = field(default_factory=dict)
    variance_analysis: Dict[str, Any] = field(default_factory=dict)
    learning_candidate: str = ""
    knowledge_item_id: Optional[str] = None
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
