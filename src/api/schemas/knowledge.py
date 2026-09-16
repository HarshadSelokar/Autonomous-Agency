"""Pydantic schemas for Phase 18 Institutional Knowledge & Organizational Experiments."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class CreateKnowledgeItemRequest(BaseModel):
    statement: str = Field(..., min_length=5, description="Factual knowledge statement")
    knowledge_type: str = Field(default="FACT", description="FACT, LESSON, PATTERN, PROCEDURAL, PREDICTION_LESSON, DECISION_LESSON, WORKFORCE_LESSON, TOOL_LESSON, MODEL_LESSON, STRATEGY_LESSON")
    scope: str = Field(default="COMPANY", description="COMPANY, DEPARTMENT, PROJECT, TEAM, EMPLOYEE, TASK, TECHNOLOGY, TOOL, MODEL, ENVIRONMENT")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source_type: str = Field(default="TASK_EXECUTION")
    task_id: str | None = None
    employee_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class ValidateKnowledgeRequest(BaseModel):
    validator_id: str = Field(..., description="Employee or System ID conducting validation")
    evidence_ids: list[str] = Field(..., description="List of evidence document or log IDs")
    rationale: str = Field(default="Independent evidence validation completed.")


class ResolveConflictRequest(BaseModel):
    resolution_strategy: str = Field(..., description="Strategy used to resolve conflict")
    winning_knowledge_id: str = Field(..., description="ID of winning knowledge item")


class CreateProcedureRequest(BaseModel):
    title: str = Field(..., min_length=3)
    purpose: str = Field(..., min_length=5)
    steps: list[dict[str, Any]] = Field(..., min_length=1)
    expected_outcome: str = Field(...)
    scope: str = Field(default="COMPANY")
    prerequisites: list[str] = Field(default_factory=list)
    verification_criteria: list[str] = Field(default_factory=list)


class ProposeExperimentRequest(BaseModel):
    title: str = Field(..., min_length=3)
    hypothesis: str = Field(..., min_length=5)
    scope: str = Field(default="COMPANY")
    risk_level: str = Field(default="LOW", description="LOW, MEDIUM, HIGH, CRITICAL")
    baseline_metrics: dict[str, Any] = Field(default_factory=dict)
    treatment_params: dict[str, Any] = Field(default_factory=dict)
    success_criteria: dict[str, Any] = Field(default_factory=dict)


class StartExperimentRequest(BaseModel):
    governance_approval_id: str | None = Field(default=None, description="Required for HIGH or CRITICAL risk experiments")


class CompleteExperimentRequest(BaseModel):
    results: dict[str, Any] = Field(..., description="Empirical metric findings")
    conclusion: str = Field(..., description="Summary of experiment outcome")


class KnowledgeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    statement: str
    knowledge_type: str
    scope: str
    authority: str
    status: str
    confidence: float
    created_at: datetime


class KnowledgeValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    knowledge_id: str
    validator_id: str
    validation_status: str
    rationale: str
    evidence_ids: list[str]
    created_at: datetime


class KnowledgeConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    knowledge_id_a: str
    knowledge_id_b: str
    status: str
    resolution_strategy: str | None = None
    winning_knowledge_id: str | None = None
    created_at: datetime


class ProcedureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    purpose: str
    version: int
    steps: list[dict[str, Any]]
    expected_outcome: str
    is_governance_approved: bool
    validation_status: str
    created_at: datetime


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    hypothesis: str
    status: str
    risk_level: str
    is_isolated: bool
    governance_approval_id: str | None
    treatment_params: dict[str, Any]
    results: dict[str, Any]
    conclusion: str | None
    created_at: datetime
