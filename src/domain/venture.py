"""
Phase 28 — Autonomous Innovation, New Venture Creation & Governed Company Expansion Domain Models.

Enforces fundamental invariants:
- IDEA != OPPORTUNITY != VALIDATED OPPORTUNITY != BUSINESS
- BUSINESS HYPOTHESIS != BUSINESS FACT
- RESEARCH != VALIDATION != EXPERIMENT != SIMULATION != REALITY
- BUSINESS CASE != GUARANTEED OUTCOME
- PROPOSAL != DECISION != AUTHORIZATION != EXECUTION
- VENTURE PROPOSAL != COMPANY
- AGENT RECOMMENDATION != AUTHORITY
- Direct execution without governance approval ID raises UnauthorizedVentureCreationError (HTTP 403)
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from src.domain.exceptions import (
    InvalidVentureLifecycleError,
    UnauthorizedVentureCreationError,
    VentureLaunchBlockedError,
)


class OpportunityStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    ANALYZING = "ANALYZING"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    CONVERTED_TO_IDEA = "CONVERTED_TO_IDEA"
    ARCHIVED = "ARCHIVED"


class VentureType(str, Enum):
    NEW_COMPANY = "NEW_COMPANY"
    NEW_SUBSIDIARY = "NEW_SUBSIDIARY"
    NEW_BUSINESS_UNIT = "NEW_BUSINESS_UNIT"
    NEW_PRODUCT_LINE = "NEW_PRODUCT_LINE"
    NEW_INTERNAL_VENTURE = "NEW_INTERNAL_VENTURE"
    SPINOUT_CANDIDATE = "SPINOUT_CANDIDATE"
    JOINT_VENTURE_CANDIDATE = "JOINT_VENTURE_CANDIDATE"


class VentureStage(str, Enum):
    DISCOVERY = "DISCOVERY"
    VALIDATION = "VALIDATION"
    EXPERIMENT = "EXPERIMENT"
    BUSINESS_CASE = "BUSINESS_CASE"
    PROPOSAL = "PROPOSAL"
    GOVERNANCE = "GOVERNANCE"
    INITIALIZATION = "INITIALIZATION"
    LAUNCH = "LAUNCH"
    EARLY_OPERATION = "EARLY_OPERATION"
    SCALING = "SCALING"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class HypothesisStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REVIEWING = "REVIEWING"
    TESTING = "TESTING"
    VALIDATED = "VALIDATED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class BusinessCaseStatus(str, Enum):
    DRAFT = "DRAFT"
    ANALYZING = "ANALYZING"
    VALIDATING = "VALIDATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED_FOR_PROPOSAL = "APPROVED_FOR_PROPOSAL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class ProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    GOVERNANCE_PENDING = "GOVERNANCE_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"
    EXPIRED = "EXPIRED"


class LaunchReadinessStatus(str, Enum):
    NOT_READY = "NOT_READY"
    ASSESSING = "ASSESSING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    LAUNCHED = "LAUNCHED"


class VentureOutcomeStatus(str, Enum):
    INITIAL = "INITIAL"
    MEASURING = "MEASURING"
    EVALUATED = "EVALUATED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    MIXED = "MIXED"


@dataclass
class InnovationOpportunity:
    """Discovered market signal or unmet customer demand opportunity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    description: str = ""
    source: str = "RESEARCH_SIGNAL"  # e.g., RESEARCH, CUSTOMER_FEEDBACK, GTM_ANALYTICS, INTELLIGENCE
    problem_statement: str = ""
    customer_need: str = ""
    market_signal: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    strategic_relevance: float = 0.80
    confidence: float = 0.50
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    potential_impact: str = ""
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InnovationIdea:
    """Proposed solution concept addressing an InnovationOpportunity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    company_id: str = ""
    title: str = ""
    description: str = ""
    proposed_solution: str = ""
    target_customer: str = ""
    value_proposition: str = ""
    differentiator: str = ""
    assumptions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BusinessHypothesis:
    """Explicit testable assumption driving an innovation idea."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idea_id: str = ""
    company_id: str = ""
    assumption: str = ""
    supporting_evidence: List[str] = field(default_factory=list)
    confidence: float = 0.50
    validation_method: str = "RESEARCH_AND_SIMULATION"
    failure_condition: str = ""
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProductConcept:
    """Structured product specification concept for a proposed venture."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idea_id: str = ""
    company_id: str = ""
    name: str = ""
    target_segment: str = ""
    capabilities: List[str] = field(default_factory=list)
    value_proposition: str = ""
    pricing_hypothesis: Dict[str, Any] = field(default_factory=dict)
    distribution_channel: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class BusinessModelConcept:
    """Economic model hypothesis for revenue, pricing, cost structure, and margins."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    idea_id: str = ""
    company_id: str = ""
    revenue_model: str = "SUBSCRIPTION"  # e.g., SUBSCRIPTION, TRANSACTIONAL, USAGE_BASED
    pricing_model: Dict[str, Any] = field(default_factory=dict)
    acquisition_strategy: str = ""
    cost_structure: Dict[str, Any] = field(default_factory=dict)
    gross_margin_est: float = 0.70
    operating_model: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureBusinessCase:
    """Comprehensive business case synthesizing market, product, financial, and workforce models."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    company_id: str = ""
    title: str = ""
    market_assumptions: Dict[str, Any] = field(default_factory=dict)
    financial_model: Dict[str, Any] = field(default_factory=dict)
    workforce_reqs: Dict[str, Any] = field(default_factory=dict)
    infra_reqs: Dict[str, Any] = field(default_factory=dict)
    risk_analysis: Dict[str, Any] = field(default_factory=dict)
    scenarios: Dict[str, Any] = field(default_factory=dict)  # BASELINE vs CONSERVATIVE vs AGGRESSIVE
    expected_roi: float = 0.35
    uncertainty_score: float = 0.25
    status: BusinessCaseStatus = BusinessCaseStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InnovationValidation:
    """Empirical validation record summarizing research, prototype, and experiment findings."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    company_id: str = ""
    validation_method: str = ""
    evidence_summary: str = ""
    confidence_score: float = 0.85
    unresolved_assumptions: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureExperiment:
    """Bounded, governed experiment testing a specific business hypothesis."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    hypothesis: str = ""
    control_config: Dict[str, Any] = field(default_factory=dict)
    treatment_config: Dict[str, Any] = field(default_factory=dict)
    duration_days: int = 7
    metrics: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    status: str = "SCHEDULED"  # SCHEDULED, RUNNING, COMPLETED, FAILED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InnovationReview:
    """Multi-dimensional review score across strategic, customer, technical, and economic criteria."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    strategic_fit_score: float = 0.85
    customer_value_score: float = 0.90
    technical_feasibility_score: float = 0.80
    economic_viability_score: float = 0.75
    risk_score: float = 0.30
    overall_score: float = 0.82
    recommendation: str = "PROCEED_TO_GOVERNANCE"
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureProposal:
    """Formal governed proposal for creating a new business unit, subsidiary, or company."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    company_id: str = ""
    title: str = ""
    venture_type: VentureType = VentureType.NEW_COMPANY
    business_case_id: str = ""
    required_budget_usd: int = 15000000  # cents (e.g. $150,000)
    required_workforce_count: int = 4
    risk_level: str = "MEDIUM"
    status: ProposalStatus = ProposalStatus.PROPOSED
    governance_required: bool = True
    governance_approval_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def assert_valid_for_initialization(self) -> None:
        """Enforces the fundamental safety invariant: venture cannot initialize without governance approval."""
        if self.governance_required and not self.governance_approval_id:
            raise UnauthorizedVentureCreationError(
                proposal_id=self.id,
                reason="Human governance approval strictly required prior to venture initialization or company creation."
            )

    def transition_status(self, target_status: ProposalStatus) -> None:
        """Enforces valid status transitions for venture proposals."""
        valid_map = {
            ProposalStatus.PROPOSED: [ProposalStatus.UNDER_REVIEW, ProposalStatus.GOVERNANCE_PENDING, ProposalStatus.REJECTED],
            ProposalStatus.UNDER_REVIEW: [ProposalStatus.GOVERNANCE_PENDING, ProposalStatus.REJECTED, ProposalStatus.DEFERRED],
            ProposalStatus.GOVERNANCE_PENDING: [ProposalStatus.APPROVED, ProposalStatus.REJECTED, ProposalStatus.DEFERRED],
            ProposalStatus.APPROVED: [ProposalStatus.EXPIRED],
            ProposalStatus.REJECTED: [],
            ProposalStatus.DEFERRED: [ProposalStatus.UNDER_REVIEW, ProposalStatus.REJECTED],
            ProposalStatus.EXPIRED: [],
        }
        allowed = valid_map.get(self.status, [])
        if target_status not in allowed:
            raise InvalidVentureLifecycleError(
                proposal_id=self.id,
                current_status=self.status.value if hasattr(self.status, "value") else str(self.status),
                target_status=target_status.value if hasattr(target_status, "value") else str(target_status),
            )
        self.status = target_status
        self.updated_at = datetime.now(UTC)


@dataclass
class VentureInitializationPlan:
    """Blueprint for creating organizational structure, departments, workforce, and product setup."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    target_structure: VentureType = VentureType.NEW_COMPANY
    departments: List[str] = field(default_factory=list)
    workforce_plan: Dict[str, Any] = field(default_factory=dict)
    product_config: Dict[str, Any] = field(default_factory=dict)
    financial_setup: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureResourceRequest:
    """Explicit request for workforce, compute, storage, and model quotas."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    workforce_count: int = 3
    model_budget_usd: int = 500000  # cents ($5,000)
    storage_gb: int = 100
    compute_cores: int = 16
    status: str = "PENDING"  # PENDING, ALLOCATED, DENIED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureResourceConflict:
    """Structured conflict when multiple ventures compete for capacity."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    competing_venture_ids: List[str] = field(default_factory=list)
    resource_type: str = "WORKFORCE"
    conflict_description: str = ""
    status: str = "OPEN"  # OPEN, RESOLVED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureLaunchReadiness:
    """Deterministic checklist required prior to production venture launch."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str = ""
    company_id: str = ""
    product_ready: bool = False
    technical_ready: bool = False
    security_ready: bool = False
    financial_ready: bool = False
    governance_ready: bool = False
    status: LaunchReadinessStatus = LaunchReadinessStatus.NOT_READY
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def evaluate_readiness(self) -> LaunchReadinessStatus:
        if (
            self.product_ready
            and self.technical_ready
            and self.security_ready
            and self.financial_ready
            and self.governance_ready
        ):
            self.status = LaunchReadinessStatus.READY
        else:
            self.status = LaunchReadinessStatus.BLOCKED
        return self.status


@dataclass
class VentureOutcome:
    """Post-launch operational & ROI measurement evaluating expected vs actual performance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    venture_id: str = ""
    company_id: str = ""
    expected_outcomes: Dict[str, Any] = field(default_factory=dict)
    actual_outcomes: Dict[str, Any] = field(default_factory=dict)
    variance_analysis: Dict[str, Any] = field(default_factory=dict)
    status: VentureOutcomeStatus = VentureOutcomeStatus.INITIAL
    measured_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class VentureScalingProposal:
    """Governed proposal to scale workforce, marketing, or infrastructure for an active venture."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    venture_id: str = ""
    company_id: str = ""
    scaling_type: str = "WORKFORCE_EXPANSION"
    resource_expansion: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    status: str = "PROPOSED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InnovationPortfolio:
    """Portfolio-level summary of active ventures, opportunities, and ROI across a company."""
    company_id: str = ""
    opportunities_count: int = 0
    active_ventures_count: int = 0
    total_budget_allocated: int = 0
    learnings_count: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
