"""Pydantic schemas for Phase 19 Research, Discovery & Innovation Engine."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CreateResearchRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Core research question to be answered")
    purpose: str = Field(..., min_length=5, description="Strategic purpose and context")
    scope: str = Field(default="COMPANY", description="COMPANY, DEPARTMENT, PROJECT, TASK, TECHNOLOGY, TOOL, MODEL, PRODUCT, WORKFORCE, STRATEGY")
    urgency: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    requester_id: str = Field(default="system")
    source_origin: str = Field(default="STRATEGY")
    governance_required: bool = Field(default=False)


class DecomposeRequestSchema(BaseModel):
    sub_questions: list[str] = Field(default_factory=list, description="Optional sub-questions to formulate")


class CreateResearchPlanRequest(BaseModel):
    question_id: str = Field(..., description="ID of research question")
    title: str = Field(..., min_length=3)
    objective: str = Field(..., min_length=5)
    required_capabilities: list[str] = Field(default_factory=list)


class RegisterSourceRequest(BaseModel):
    location: str = Field(..., min_length=1, description="URI, path, or URL of source")
    source_type: str = Field(default="TECHNICAL_DOCUMENTATION", description="INTERNAL_DOCUMENT, INTERNAL_ARTIFACT, INTERNAL_DATASET, APPROVED_EXTERNAL_WEBSITE, EXTERNAL_API, TECHNICAL_DOCUMENTATION, PUBLIC_RESEARCH_PAPER, APPROVED_DATABASE")
    provenance: str = Field(default="")
    raw_content: str = Field(default="")
    is_external: bool = Field(default=False)


class AddEvidenceRequest(BaseModel):
    source_id: str = Field(..., description="Source ID where snippet originated")
    content_snippet: str = Field(..., min_length=5)
    data_points: dict[str, Any] = Field(default_factory=dict)


class SynthesizeFindingRequest(BaseModel):
    question_id: str = Field(..., description="Research question ID")
    finding_statement: str = Field(..., min_length=5)
    evidence_ids: list[str] = Field(..., min_length=1, description="Must reference at least 1 evidence item")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    researcher_id: str = Field(default="system")


class FormulateHypothesisRequest(BaseModel):
    question_id: str = Field(..., description="Research question ID")
    observation: str = Field(..., min_length=5)
    statement: str = Field(..., min_length=5)
    prediction: str = Field(..., min_length=5)


class EvaluateHypothesisRequest(BaseModel):
    result_description: str = Field(..., min_length=5)
    conclusion: str = Field(..., min_length=5)
    is_supported: bool = Field(...)


class IdentifyOpportunityRequest(BaseModel):
    finding_id: str = Field(..., description="Finding ID driving opportunity")
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    estimated_value_score: float = Field(default=0.8, ge=0.0, le=1.0)


class CreateInnovationProposalRequest(BaseModel):
    opportunity_id: str = Field(..., description="Opportunity ID")
    title: str = Field(..., min_length=3)
    innovation_type: str = Field(default="PRODUCT_INNOVATION", description="PRODUCT_INNOVATION, PROCESS_INNOVATION, TECHNOLOGY_INNOVATION, WORKFLOW_INNOVATION, MODEL_ROUTING_INNOVATION, ARCHITECTURE_INNOVATION")
    problem_statement: str = Field(..., min_length=5)
    proposed_solution: str = Field(..., min_length=5)
    expected_value: str = Field(..., min_length=3)
    evidence_ids: list[str] = Field(..., min_length=1)
    reversibility: str = Field(default="HIGH", description="HIGH, MEDIUM, LOW")


class ApproveProposalRequest(BaseModel):
    governance_request_id: str = Field(..., description="Phase 11 Governance approval ID")


class ResearchRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    purpose: str
    scope: str
    urgency: str
    requester_id: str
    source_origin: str
    status: str
    governance_required: bool
    created_at: datetime


class InnovationProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    title: str
    innovation_type: str
    problem_statement: str
    evidence_ids: list[str]
    proposed_solution: str
    expected_value: str
    reversibility: str
    governance_request_id: str | None = None
    is_approved: bool
    strategic_initiative_id: str | None = None
    created_at: datetime
