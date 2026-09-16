"""SQLAlchemy ORM Models for Phase 19 Research, Discovery & Innovation Engine."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class ResearchProgramModel(Base):
    __tablename__ = "research_programs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPANY")
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, default="system")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    research_question_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    findings_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    knowledge_item_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchRequestModel(Base):
    __tablename__ = "research_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPANY")
    urgency: Mapped[str] = mapped_column(String(50), nullable=False, default="MEDIUM")
    requester_id: Mapped[str] = mapped_column(String(36), nullable=False, default="system")
    source_origin: Mapped[str] = mapped_column(String(50), nullable=False, default="STRATEGY")
    expected_output: Mapped[str] = mapped_column(Text, nullable=False, default="")
    constraints: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evidence_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="REQUESTED")
    governance_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchQuestionModel(Base):
    __tablename__ = "research_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assumptions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPANY")
    evidence_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    success_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    parent_question_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    sub_question_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, default="system")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchPlanModel(Base):
    __tablename__ = "research_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False, default="")
    task_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    assigned_employee_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    assigned_team_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tool_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PLANNING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchSourceModel(Base):
    __tablename__ = "research_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    location: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="INTERNAL_DOCUMENT")
    access_method: Mapped[str] = mapped_column(String(50), nullable=False, default="READ")
    provenance: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_external: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_untrusted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    prompt_injection_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchEvidenceModel(Base):
    __tablename__ = "research_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    content_snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    data_points: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    integrity_hash: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    is_independent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    corroboration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchFindingModel(Base):
    __tablename__ = "research_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(String(36), nullable=False)
    finding_statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPANY")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    assumptions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    limitations: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    researcher_id: Mapped[str] = mapped_column(String(36), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchHypothesisModel(Base):
    __tablename__ = "research_hypotheses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    question_id: Mapped[str] = mapped_column(String(36), nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    prediction: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROPOSED")
    experiment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchBenchmarkModel(Base):
    __tablename__ = "research_benchmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    benchmark_type: Mapped[str] = mapped_column(String(50), nullable=False, default="MODEL_PERFORMANCE")
    target_name: Mapped[str] = mapped_column(String(255), nullable=False)
    workload_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    environment: Mapped[str] = mapped_column(String(100), nullable=False, default="TEST")
    limitations: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class TechnologyEvaluationModel(Base):
    __tablename__ = "technology_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    candidate_technology: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="FRAMEWORK")
    benchmark_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    security_review_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cost_analysis: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    operational_feasibility: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    governance_approval_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchDiscoveryModel(Base):
    __tablename__ = "research_discoveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trigger_event: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ResearchOpportunityModel(Base):
    __tablename__ = "research_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    finding_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IDENTIFIED")
    estimated_value_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class InnovationProposalModel(Base):
    __tablename__ = "innovation_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    innovation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="TECHNOLOGY_INNOVATION")
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    proposed_solution: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    required_capabilities: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    required_resources: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    reversibility: Mapped[str] = mapped_column(String(50), nullable=False, default="HIGH")
    governance_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    strategic_initiative_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
