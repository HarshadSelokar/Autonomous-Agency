"""
Strategy & Strategic Intelligence Domain Module.

Defines entities, value objects, and enums for Company Strategy versioning,
Strategic Objectives, Strategic Initiatives, Strategic Analysis, Strategy Proposals,
and isolated What-If Strategy Simulations.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class StrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ROLLED_BACK = "ROLLED_BACK"


class StrategyProposalType(str, Enum):
    REPRIORITIZE_OBJECTIVES = "REPRIORITIZE_OBJECTIVES"
    CREATE_INITIATIVE = "CREATE_INITIATIVE"
    PAUSE_INITIATIVE = "PAUSE_INITIATIVE"
    PROJECT_PRIORITY_CHANGE = "PROJECT_PRIORITY_CHANGE"
    WORKFORCE_REQUEST = "WORKFORCE_REQUEST"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    QUALITY_PROGRAM = "QUALITY_PROGRAM"
    POLICY_CHANGE = "POLICY_CHANGE"
    ORGANIZATIONAL_EVOLUTION = "ORGANIZATIONAL_EVOLUTION"


class StrategyProposalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


@dataclass
class StrategicObjective:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    description: str = ""
    target_metric: str = ""
    target_value: float = 100.0
    current_value: float = 0.0
    priority: int = 1
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StrategicInitiative:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategic_objective_id: str = ""
    title: str = ""
    description: str = ""
    lead_department_id: str | None = None
    project_ids: list[str] = field(default_factory=list)
    status: str = "PROPOSED"
    budget_tokens: int = 1000000
    spent_tokens: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyStrategy:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    version: int = 1
    title: str = "Default Company Strategy"
    themes: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)
    targets: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    status: StrategyStatus = StrategyStatus.ACTIVE
    proposer_id: str = "system"
    approved_by_id: str | None = None
    previous_version_id: str | None = None
    change_rationale: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StrategicAnalysis:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    cycle_id: str | None = None
    current_situation: str = ""
    observed_facts: list[str] = field(default_factory=list)
    trends: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    potential_causes: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    required_resources: str = ""
    confidence: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)
    model_used: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class StrategyProposal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    proposal_type: StrategyProposalType = StrategyProposalType.REPRIORITIZE_OBJECTIVES
    title: str = ""
    proposal: str = ""
    reason: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    benefits: str = ""
    resource_impact: str = ""
    risks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    affected_departments: list[str] = field(default_factory=list)
    reversibility: str = "HIGH"  # HIGH, MEDIUM, LOW
    governance_level: str = "MANAGER_APPROVAL"  # LOW, MANAGER_APPROVAL, HUMAN_GOVERNANCE_REQUIRED
    confidence: float = 1.0
    status: StrategyProposalStatus = StrategyProposalStatus.PROPOSED
    proposed_by_id: str = ""
    governance_approval_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None


@dataclass
class StrategySimulation:
    """
    Isolated what-if planning simulation.
    MUST NEVER mutate authoritative company state.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    title: str = ""
    assumptions: list[str] = field(default_factory=list)
    input_parameters: dict[str, Any] = field(default_factory=dict)
    projected_outcomes: dict[str, Any] = field(default_factory=dict)
    resource_effects: dict[str, Any] = field(default_factory=dict)
    projected_risks: list[str] = field(default_factory=list)
    confidence: float = 1.0
    is_authoritative: bool = False  # Invariant: ALWAYS False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.is_authoritative:
            raise ValueError("Simulation state cannot be declared authoritative!")
