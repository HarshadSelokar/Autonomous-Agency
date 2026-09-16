"""Pydantic schemas for Phase 16 Autonomous Company API."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CreateCompanyRequest(BaseModel):
    name: str = Field(..., description="Company name")
    code: str = Field(..., description="Company ticker/code e.g. AUTOCORP")
    mission: str = Field("", description="Company mission statement")
    settings: dict[str, Any] = Field(default_factory=dict)


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    mission: str
    status: str
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class StartOperatingCycleRequest(BaseModel):
    initiated_by_id: str = Field("system", description="User or agent ID initiating cycle")


class TransitionCycleStateRequest(BaseModel):
    target_state: str = Field(..., description="Target OperatingCycleState")
    checkpoint_data: dict[str, Any] = Field(default_factory=dict)


class CompanyOperatingCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    cycle_number: int
    state: str
    checkpoint_data: dict[str, Any]
    initiated_by_id: str
    started_at: datetime
    completed_at: datetime | None = None
    failure_reason: str | None = None


class CreateStrategyRequest(BaseModel):
    title: str = Field(..., description="Strategy title")
    themes: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    targets: dict[str, Any] = Field(default_factory=dict)
    change_rationale: str = Field("", description="Rationale for strategy version change")


class CompanyStrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    version: int
    title: str
    themes: list[str]
    constraints: list[str]
    priorities: list[str]
    targets: dict[str, Any]
    status: str
    proposer_id: str
    approved_by_id: str | None = None
    previous_version_id: str | None = None
    change_rationale: str
    created_at: datetime


class CreateStrategyProposalRequest(BaseModel):
    proposal_type: str = Field(..., description="StrategyProposalType e.g. ORGANIZATIONAL_EVOLUTION")
    title: str = Field(..., description="Proposal title")
    proposal_body: str = Field(..., description="Detailed proposal body")
    reason: str = Field(..., description="Strategic rationale")
    benefits: str = Field("", description="Expected benefits")
    resource_impact: str = Field("", description="Estimated resource impact")
    governance_level: str = Field("EXECUTIVE_APPROVAL", description="Governance approval level required")


class StrategyProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    proposal_type: str
    title: str
    proposal: str
    reason: str
    benefits: str
    resource_impact: str
    risks: list[str]
    governance_level: str
    confidence: float
    status: str
    proposed_by_id: str
    governance_approval_id: str | None = None
    created_at: datetime


class RunSimulationRequest(BaseModel):
    title: str = Field(..., description="Scenario title")
    assumptions: list[str] = Field(default_factory=list)
    input_parameters: dict[str, Any] = Field(default_factory=dict)


class StrategySimulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    title: str
    assumptions: list[str]
    input_parameters: dict[str, Any]
    projected_outcomes: dict[str, Any]
    resource_effects: dict[str, Any]
    projected_risks: list[str]
    confidence: float
    is_authoritative: bool = False
    created_at: datetime


class CompanyHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    operational_health: float
    execution_health: float
    delivery_health: float
    quality_health: float
    workforce_health: float
    reliability_health: float
    resource_health: float
    governance_health: float
    security_health: float
    overall_status: str
    explanation: str
    evaluated_at: datetime


class ExecutiveReportResponse(BaseModel):
    report_id: str
    company_id: str
    company_name: str
    code: str
    cycle_id: str | None = None
    generated_at: str
    active_strategy: dict[str, Any]
    health: dict[str, Any]
    objectives_count: int
    open_risks_count: int
    opportunities_count: int
    portfolio_items_count: int
    bottlenecks: list[str]


class CreatePortfolioItemRequest(BaseModel):
    title: str = Field(..., description="Portfolio item name")
    reference_id: str = Field(..., description="Underlying project or initiative ID")
    item_type: str = Field("PROJECT", description="ITEM type")
    priority: int = Field(1, description="Priority rank")


class PortfolioItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    title: str
    item_type: str
    reference_id: str
    priority: int
    progress_pct: float
    resource_utilization_pct: float
    status: str
    has_bottleneck: bool
    bottleneck_description: str | None = None
    created_at: datetime
