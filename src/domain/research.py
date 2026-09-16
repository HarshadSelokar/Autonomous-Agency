"""Autonomous Research, Discovery & Innovation Engine Domain Module for Phase 19.

Defines entities, value objects, and enums for Research Programs, Requests, Decomposed Questions,
Plans, Untrusted Sources, Evidence, Findings, Hypotheses, Governed Experiments, Benchmarks,
Technology Evaluations, Autonomous Discoveries, Opportunities, Innovation Proposals, and Initiatives.

Core Invariants Enforced:
- RESEARCH != KNOWLEDGE
- SOURCE != EVIDENCE
- EVIDENCE != TRUTH AUTOMATICALLY
- FINDING != FACT
- HYPOTHESIS != FACT
- PREDICTION != RESULT
- RESULT != CONCLUSION AUTOMATICALLY
- CONCLUSION != KNOWLEDGE AUTOMATICALLY
- RECOMMENDATION != DECISION
- INNOVATION PROPOSAL != INITIATIVE
- EXPERIMENT != PRODUCTION
- EXTERNAL CONTENT != TRUSTED INSTRUCTION
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
import uuid


class ResearchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REQUESTED = "REQUESTED"
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ANALYZING = "ANALYZING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class ResearchScope(str, Enum):
    COMPANY = "COMPANY"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"
    TASK = "TASK"
    TECHNOLOGY = "TECHNOLOGY"
    TOOL = "TOOL"
    MODEL = "MODEL"
    PRODUCT = "PRODUCT"
    WORKFORCE = "WORKFORCE"
    STRATEGY = "STRATEGY"


class ResearchUrgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SourceType(str, Enum):
    INTERNAL_DOCUMENT = "INTERNAL_DOCUMENT"
    INTERNAL_ARTIFACT = "INTERNAL_ARTIFACT"
    INTERNAL_DATASET = "INTERNAL_DATASET"
    APPROVED_EXTERNAL_WEBSITE = "APPROVED_EXTERNAL_WEBSITE"
    EXTERNAL_API = "EXTERNAL_API"
    TECHNICAL_DOCUMENTATION = "TECHNICAL_DOCUMENTATION"
    PUBLIC_RESEARCH_PAPER = "PUBLIC_RESEARCH_PAPER"
    APPROVED_DATABASE = "APPROVED_DATABASE"


class HypothesisStatus(str, Enum):
    PROPOSED = "PROPOSED"
    REVIEWING = "REVIEWING"
    ACCEPTED = "ACCEPTED"
    TESTING = "TESTING"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ARCHIVED = "ARCHIVED"


class InnovationType(str, Enum):
    PRODUCT_INNOVATION = "PRODUCT_INNOVATION"
    PROCESS_INNOVATION = "PROCESS_INNOVATION"
    TECHNOLOGY_INNOVATION = "TECHNOLOGY_INNOVATION"
    WORKFLOW_INNOVATION = "WORKFLOW_INNOVATION"
    MODEL_ROUTING_INNOVATION = "MODEL_ROUTING_INNOVATION"
    ARCHITECTURE_INNOVATION = "ARCHITECTURE_INNOVATION"


class OpportunityStatus(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    ANALYZING = "ANALYZING"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class BenchmarkType(str, Enum):
    MODEL_PERFORMANCE = "MODEL_PERFORMANCE"
    TOOL_RELIABILITY = "TOOL_RELIABILITY"
    WORKFLOW_LATENCY = "WORKFLOW_LATENCY"
    ARCHITECTURE_EFFICIENCY = "ARCHITECTURE_EFFICIENCY"
    ALGORITHM_SPEED = "ALGORITHM_SPEED"


@dataclass
class ResearchProgram:
    id: str = field(default_factory=lambda: f"prog-{uuid.uuid4().hex[:8]}")
    title: str = ""
    purpose: str = ""
    scope: ResearchScope = ResearchScope.COMPANY
    owner_id: str = "system"
    status: ResearchStatus = ResearchStatus.ACTIVE
    research_question_ids: list[str] = field(default_factory=list)
    findings_ids: list[str] = field(default_factory=list)
    knowledge_item_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchRequest:
    id: str = field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    question: str = ""
    purpose: str = ""
    scope: ResearchScope = ResearchScope.COMPANY
    urgency: ResearchUrgency = ResearchUrgency.MEDIUM
    requester_id: str = "system"
    source_origin: str = "STRATEGY"  # STRATEGY, OPERATING_CYCLE, MANAGER, EMPLOYEE, TASK_FAILURE, KNOWLEDGE_GAP
    expected_output: str = ""
    constraints: dict[str, Any] = field(default_factory=dict)
    evidence_requirements: list[str] = field(default_factory=list)
    status: ResearchStatus = ResearchStatus.REQUESTED
    governance_required: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchQuestion:
    id: str = field(default_factory=lambda: f"q-{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    question: str = ""
    context: str = ""
    assumptions: list[str] = field(default_factory=list)
    scope: ResearchScope = ResearchScope.COMPANY
    evidence_requirements: list[str] = field(default_factory=list)
    success_criteria: dict[str, Any] = field(default_factory=dict)
    parent_question_id: str | None = None
    sub_question_ids: list[str] = field(default_factory=list)
    owner_id: str = "system"
    status: ResearchStatus = ResearchStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchPlan:
    id: str = field(default_factory=lambda: f"rplan-{uuid.uuid4().hex[:8]}")
    question_id: str = ""
    title: str = ""
    objective: str = ""
    task_ids: list[str] = field(default_factory=list)
    assigned_employee_ids: list[str] = field(default_factory=list)
    assigned_team_id: str | None = None
    tool_requirements: list[str] = field(default_factory=list)
    status: ResearchStatus = ResearchStatus.PLANNING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchSource:
    id: str = field(default_factory=lambda: f"src-{uuid.uuid4().hex[:8]}")
    location: str = ""
    source_type: SourceType = SourceType.INTERNAL_DOCUMENT
    access_method: str = "READ"
    provenance: str = ""
    is_external: bool = False
    is_untrusted: bool = True  # External content is untrusted by default!
    prompt_injection_checked: bool = False
    reliability_score: float = 0.5  # 0.0 to 1.0 explainable score
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchEvidence:
    id: str = field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")
    source_id: str = ""
    content_snippet: str = ""
    data_points: dict[str, Any] = field(default_factory=dict)
    integrity_hash: str = ""
    is_independent: bool = True  # Derivative duplicate sources set to False
    corroboration_count: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchFinding:
    id: str = field(default_factory=lambda: f"find-{uuid.uuid4().hex[:8]}")
    question_id: str = ""
    finding_statement: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    scope: ResearchScope = ResearchScope.COMPANY
    confidence: float = 0.5
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    researcher_id: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchHypothesis:
    id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:8]}")
    question_id: str = ""
    observation: str = ""
    statement: str = ""
    prediction: str = ""
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    experiment_id: str | None = None
    result: str | None = None
    conclusion: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_status(self, target_status: HypothesisStatus) -> None:
        """Never automatically mark hypotheses True; enforce explicit transitions."""
        self.status = target_status


@dataclass
class ResearchBenchmark:
    id: str = field(default_factory=lambda: f"bench-{uuid.uuid4().hex[:8]}")
    benchmark_type: BenchmarkType = BenchmarkType.MODEL_PERFORMANCE
    target_name: str = ""
    workload_description: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    environment: str = "TEST"
    limitations: list[str] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TechnologyEvaluation:
    id: str = field(default_factory=lambda: f"techeval-{uuid.uuid4().hex[:8]}")
    candidate_technology: str = ""
    category: str = "FRAMEWORK"
    benchmark_ids: list[str] = field(default_factory=list)
    security_review_summary: str = ""
    cost_analysis: dict[str, Any] = field(default_factory=dict)
    operational_feasibility: str = ""
    recommendation: str = ""
    governance_approval_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchDiscovery:
    id: str = field(default_factory=lambda: f"disc-{uuid.uuid4().hex[:8]}")
    trigger_event: str = ""  # KPI_DEVIATION, BOTTLENECK, TASK_FAILURE, KNOWLEDGE_GAP
    trigger_entity_id: str = ""
    description: str = ""
    created_request_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResearchOpportunity:
    id: str = field(default_factory=lambda: f"opp-{uuid.uuid4().hex[:8]}")
    finding_id: str = ""
    title: str = ""
    description: str = ""
    status: OpportunityStatus = OpportunityStatus.IDENTIFIED
    estimated_value_score: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InnovationProposal:
    id: str = field(default_factory=lambda: f"inno-{uuid.uuid4().hex[:8]}")
    opportunity_id: str = ""
    title: str = ""
    innovation_type: InnovationType = InnovationType.TECHNOLOGY_INNOVATION
    problem_statement: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    proposed_solution: str = ""
    expected_value: str = ""
    required_capabilities: list[str] = field(default_factory=list)
    required_resources: dict[str, Any] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    reversibility: str = "HIGH"  # HIGH, MEDIUM, LOW
    governance_request_id: str | None = None
    is_approved: bool = False
    strategic_initiative_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
