"""
SQLAlchemy ORM Data Models for Phase 27 Continuous Organizational Learning & Governed Adaptation.
"""

from datetime import UTC, datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from src.infrastructure.database import Base


class LearningCycleModel(Base):
    __tablename__ = "learning_cycles"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    purpose = Column(String(256), nullable=False)
    scope = Column(String(32), nullable=False, default="COMPANY")
    environment = Column(String(32), nullable=False, default="PRODUCTION")
    simulation_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="CREATED")
    correlation_id = Column(String(64), nullable=False)
    observations_count = Column(Integer, nullable=False, default=0)
    patterns_count = Column(Integer, nullable=False, default=0)
    candidates_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LearningObservationModel(Base):
    __tablename__ = "learning_observations"

    id = Column(String(64), primary_key=True)
    cycle_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    source_subsystem = Column(String(64), nullable=False)
    entity_reference = Column(String(128), nullable=False)
    observed_value_json = Column(Text, nullable=True)
    expected_value_json = Column(Text, nullable=True)
    context_data_json = Column(Text, nullable=False, default="{}")
    provenance_json = Column(Text, nullable=False, default="{}")
    observed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ExpectedVsActualComparisonModel(Base):
    __tablename__ = "expected_vs_actual_comparisons"

    id = Column(String(64), primary_key=True)
    cycle_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    domain = Column(String(64), nullable=False)
    metric_name = Column(String(128), nullable=False)
    expected_value = Column(Float, nullable=False, default=0.0)
    actual_value = Column(Float, nullable=False, default=0.0)
    variance = Column(Float, nullable=False, default=0.0)
    variance_percentage = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.9)
    context_json = Column(Text, nullable=False, default="{}")
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LearningCandidateModel(Base):
    __tablename__ = "learning_candidates"

    id = Column(String(64), primary_key=True)
    cycle_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    statement = Column(Text, nullable=False)
    scope = Column(String(32), nullable=False, default="COMPANY")
    supporting_observation_ids_json = Column(Text, nullable=False, default="[]")
    counterexamples_json = Column(Text, nullable=False, default="[]")
    assumptions_json = Column(Text, nullable=False, default="[]")
    confidence = Column(Float, nullable=False, default=0.5)
    generated_by = Column(String(64), nullable=False, default="SYSTEM")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LearningValidationModel(Base):
    __tablename__ = "learning_validations"

    id = Column(String(64), primary_key=True)
    candidate_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    validation_method = Column(String(64), nullable=False, default="HISTORICAL_ANALYSIS")
    is_valid = Column(Boolean, nullable=False, default=False)
    evidence_score = Column(Float, nullable=False, default=0.5)
    validation_notes = Column(Text, nullable=False, default="")
    validated_by = Column(String(64), nullable=False, default="SYSTEM")
    validated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LearningConflictModel(Base):
    __tablename__ = "learning_conflicts"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    lesson_a_id = Column(String(64), nullable=False)
    lesson_b_id = Column(String(64), nullable=False)
    conflict_summary = Column(Text, nullable=False)
    context_discrepancies_json = Column(Text, nullable=False, default="[]")
    status = Column(String(32), nullable=False, default="OPEN")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LearningPatternModel(Base):
    __tablename__ = "learning_patterns"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    pattern_name = Column(String(128), nullable=False)
    pattern_type = Column(String(64), nullable=False, default="RECURRING_FAILURE")
    frequency = Column(Integer, nullable=False, default=1)
    scope = Column(String(32), nullable=False, default="COMPANY")
    confidence = Column(Float, nullable=False, default=0.85)
    evidence_references_json = Column(Text, nullable=False, default="[]")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ImprovementOpportunityModel(Base):
    __tablename__ = "improvement_opportunities"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    affected_area = Column(String(128), nullable=False)
    expected_impact = Column(Text, nullable=False)
    required_resources_json = Column(Text, nullable=False, default="{}")
    risks_json = Column(Text, nullable=False, default="[]")
    constraints_json = Column(Text, nullable=False, default="[]")
    confidence = Column(Float, nullable=False, default=0.8)
    identified_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AdaptationProposalModel(Base):
    __tablename__ = "adaptation_proposals"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    opportunity_id = Column(String(64), nullable=False)
    adaptation_type = Column(String(64), nullable=False, default="WORKFLOW_CHANGE")
    risk_level = Column(String(32), nullable=False, default="MEDIUM")
    current_state_json = Column(Text, nullable=False, default="{}")
    proposed_state_json = Column(Text, nullable=False, default="{}")
    rationale = Column(Text, nullable=False)
    rollback_plan_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="PROPOSED")
    governance_required = Column(Boolean, nullable=False, default=True)
    governance_approval_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AdaptationEvaluationModel(Base):
    __tablename__ = "adaptation_evaluations"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    expected_benefit_score = Column(Float, nullable=False, default=0.5)
    risk_score = Column(Float, nullable=False, default=0.5)
    cost_score = Column(Float, nullable=False, default=0.5)
    reversibility_score = Column(Float, nullable=False, default=0.5)
    overall_recommendation_score = Column(Float, nullable=False, default=0.5)
    evaluation_breakdown_json = Column(Text, nullable=False, default="{}")
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AdaptationExecutionModel(Base):
    __tablename__ = "adaptation_executions"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    governance_approval_id = Column(String(64), nullable=False)
    execution_type = Column(String(64), nullable=False, default="CONTROLLED_EXPERIMENT")
    target_subsystem = Column(String(64), nullable=False)
    execution_payload_json = Column(Text, nullable=False, default="{}")
    dispatched_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AdaptationOutcomeModel(Base):
    __tablename__ = "adaptation_outcomes"

    id = Column(String(64), primary_key=True)
    execution_id = Column(String(64), nullable=False)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    expected_metrics_json = Column(Text, nullable=False, default="{}")
    actual_metrics_json = Column(Text, nullable=False, default="{}")
    variance_analysis_json = Column(Text, nullable=False, default="{}")
    side_effects_detected_json = Column(Text, nullable=False, default="[]")
    has_regression = Column(Boolean, nullable=False, default=False)
    measured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AdaptationImpactAssessmentModel(Base):
    __tablename__ = "adaptation_impact_assessments"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    affected_subsystems_json = Column(Text, nullable=False, default="[]")
    downstream_dependencies_json = Column(Text, nullable=False, default="[]")
    rollback_feasibility_score = Column(Float, nullable=False, default=1.0)
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
