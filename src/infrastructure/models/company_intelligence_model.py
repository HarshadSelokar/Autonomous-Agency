"""
SQLAlchemy ORM Models for Phase 26 Company Intelligence & Decision Support.
"""

from datetime import UTC, datetime
from typing import Any, Dict
import json

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.infrastructure.database import Base


class IntelligenceRunModel(Base):
    __tablename__ = "intelligence_runs"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    purpose = Column(String(256), nullable=False)
    scope = Column(String(64), nullable=False, default="FULL_COMPANY")
    environment = Column(String(32), nullable=False, default="PRODUCTION")
    simulation_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="REQUESTED")
    requesting_principal = Column(String(64), nullable=False, default="SYSTEM")
    data_sources_json = Column(Text, nullable=False, default="[]")
    model_metadata_json = Column(Text, nullable=False, default="{}")
    findings_count = Column(Integer, nullable=False, default=0)
    uncertainty_score = Column(Float, nullable=False, default=0.1)
    correlation_id = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class IntelligenceFindingModel(Base):
    __tablename__ = "intelligence_findings"

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    observation_summary = Column(Text, nullable=False)
    evidence_references_json = Column(Text, nullable=False, default="[]")
    confidence = Column(Float, nullable=False, default=0.9)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DecisionQuestionModel(Base):
    __tablename__ = "decision_questions"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    question = Column(Text, nullable=False)
    purpose = Column(String(256), nullable=False)
    scope = Column(String(64), nullable=False, default="STRATEGIC")
    urgency = Column(String(32), nullable=False, default="MEDIUM")
    requester_id = Column(String(64), nullable=False, default="SYSTEM")
    constraints_json = Column(Text, nullable=False, default="[]")
    decision_deadline = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DecisionOptionModel(Base):
    __tablename__ = "decision_options"

    id = Column(String(64), primary_key=True)
    question_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    option_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    is_no_action_baseline = Column(Boolean, nullable=False, default=False)
    assumptions_json = Column(Text, nullable=False, default="[]")
    required_resources_json = Column(Text, nullable=False, default="{}")
    expected_benefits_json = Column(Text, nullable=False, default="{}")
    expected_costs_cents = Column(BigInteger, nullable=False, default=0)
    risk_factors_json = Column(Text, nullable=False, default="[]")
    dependencies_json = Column(Text, nullable=False, default="[]")
    scenario_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DecisionEvaluationModel(Base):
    __tablename__ = "decision_evaluations"

    id = Column(String(64), primary_key=True)
    option_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False)
    strategic_alignment_score = Column(Float, nullable=False, default=0.5)
    financial_impact_score = Column(Float, nullable=False, default=0.5)
    customer_impact_score = Column(Float, nullable=False, default=0.5)
    product_impact_score = Column(Float, nullable=False, default=0.5)
    workforce_impact_score = Column(Float, nullable=False, default=0.5)
    operational_risk_score = Column(Float, nullable=False, default=0.5)
    execution_complexity_score = Column(Float, nullable=False, default=0.5)
    reversibility_score = Column(Float, nullable=False, default=0.5)
    confidence_score = Column(Float, nullable=False, default=0.85)
    overall_score = Column(Float, nullable=False, default=0.5)
    evaluation_breakdown_json = Column(Text, nullable=False, default="{}")
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DecisionInsightModel(Base):
    __tablename__ = "decision_insights"

    id = Column(String(64), primary_key=True)
    question_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    evidence_graph_json = Column(Text, nullable=False, default="{}")
    options_json = Column(Text, nullable=False, default="[]")
    tradeoffs_json = Column(Text, nullable=False, default="[]")
    recommendation_summary = Column(Text, nullable=False)
    recommended_option_id = Column(String(64), nullable=True)
    uncertainty_analysis_json = Column(Text, nullable=False, default="{}")
    governance_required = Column(Boolean, nullable=False, default=True)
    governance_approval_id = Column(String(64), nullable=True)
    is_executed = Column(Boolean, nullable=False, default=False)
    is_expired = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CompanyHealthAssessmentModel(Base):
    __tablename__ = "company_health_assessments"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    overall_health_status = Column(String(32), nullable=False, default="HEALTHY")
    dimension_scores_json = Column(Text, nullable=False, default="{}")
    key_findings_json = Column(Text, nullable=False, default="[]")
    top_risks_json = Column(Text, nullable=False, default="[]")
    top_opportunities_json = Column(Text, nullable=False, default="[]")
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CompanyBottleneckModel(Base):
    __tablename__ = "company_bottlenecks"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    bottleneck_name = Column(String(128), nullable=False)
    affected_scope = Column(String(128), nullable=False)
    severity = Column(String(32), nullable=False, default="MEDIUM")
    evidence_summary = Column(Text, nullable=False)
    suspected_causes_json = Column(Text, nullable=False, default="[]")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    is_resolved = Column(Boolean, nullable=False, default=False)


class CompanyRiskAssessmentModel(Base):
    __tablename__ = "company_risk_assessments"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False, default="OPERATIONAL")
    probability_score = Column(Float, nullable=False, default=0.3)
    impact_score = Column(Float, nullable=False, default=0.5)
    severity = Column(String(32), nullable=False, default="MEDIUM")
    leading_indicators_json = Column(Text, nullable=False, default="[]")
    mitigation_options_json = Column(Text, nullable=False, default="[]")
    confidence = Column(Float, nullable=False, default=0.85)
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DecisionOutcomeEvaluationModel(Base):
    __tablename__ = "decision_outcome_evaluations"

    id = Column(String(64), primary_key=True)
    insight_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    executed_option_id = Column(String(64), nullable=False)
    expected_outcomes_json = Column(Text, nullable=False, default="{}")
    actual_outcomes_json = Column(Text, nullable=False, default="{}")
    variance_analysis_json = Column(Text, nullable=False, default="{}")
    learning_candidate = Column(Text, nullable=False)
    knowledge_item_id = Column(String(64), nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
