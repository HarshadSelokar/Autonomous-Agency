"""
SQLAlchemy ORM Models for Phase 28 Autonomous Innovation, Venture Creation & Governed Expansion.
"""

from datetime import UTC, datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from src.infrastructure.database import Base


class InnovationOpportunityModel(Base):
    __tablename__ = "innovation_opportunities"

    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(64), nullable=False, default="RESEARCH_SIGNAL")
    problem_statement = Column(Text, nullable=False)
    customer_need = Column(Text, nullable=False)
    market_signal_json = Column(Text, nullable=False, default="{}")
    evidence_json = Column(Text, nullable=False, default="[]")
    strategic_relevance = Column(Float, nullable=False, default=0.80)
    confidence = Column(Float, nullable=False, default=0.50)
    assumptions_json = Column(Text, nullable=False, default="[]")
    risks_json = Column(Text, nullable=False, default="[]")
    potential_impact = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="DISCOVERED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class InnovationIdeaModel(Base):
    __tablename__ = "innovation_ideas"

    id = Column(String(64), primary_key=True)
    opportunity_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    proposed_solution = Column(Text, nullable=False)
    target_customer = Column(Text, nullable=False)
    value_proposition = Column(Text, nullable=False)
    differentiator = Column(Text, nullable=False)
    assumptions_json = Column(Text, nullable=False, default="[]")
    dependencies_json = Column(Text, nullable=False, default="[]")
    risks_json = Column(Text, nullable=False, default="[]")
    required_capabilities_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class BusinessHypothesisModel(Base):
    __tablename__ = "business_hypotheses"

    id = Column(String(64), primary_key=True)
    idea_id = Column(String(64), nullable=False, index=True)
    company_id = Column(String(64), nullable=False, index=True)
    assumption = Column(Text, nullable=False)
    supporting_evidence_json = Column(Text, nullable=False, default="[]")
    confidence = Column(Float, nullable=False, default=0.50)
    validation_method = Column(String(64), nullable=False, default="RESEARCH_AND_SIMULATION")
    failure_condition = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="PROPOSED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ProductConceptModel(Base):
    __tablename__ = "product_concepts"

    id = Column(String(64), primary_key=True)
    idea_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    target_segment = Column(Text, nullable=False)
    capabilities_json = Column(Text, nullable=False, default="[]")
    value_proposition = Column(Text, nullable=False)
    pricing_hypothesis_json = Column(Text, nullable=False, default="{}")
    distribution_channel = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class BusinessModelConceptModel(Base):
    __tablename__ = "business_model_concepts"

    id = Column(String(64), primary_key=True)
    idea_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    revenue_model = Column(String(64), nullable=False, default="SUBSCRIPTION")
    pricing_model_json = Column(Text, nullable=False, default="{}")
    acquisition_strategy = Column(Text, nullable=False)
    cost_structure_json = Column(Text, nullable=False, default="{}")
    gross_margin_est = Column(Float, nullable=False, default=0.70)
    operating_model = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureBusinessCaseModel(Base):
    __tablename__ = "venture_business_cases"

    id = Column(String(64), primary_key=True)
    opportunity_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    market_assumptions_json = Column(Text, nullable=False, default="{}")
    financial_model_json = Column(Text, nullable=False, default="{}")
    workforce_reqs_json = Column(Text, nullable=False, default="{}")
    infra_reqs_json = Column(Text, nullable=False, default="{}")
    risk_analysis_json = Column(Text, nullable=False, default="{}")
    scenarios_json = Column(Text, nullable=False, default="{}")
    expected_roi = Column(Float, nullable=False, default=0.35)
    uncertainty_score = Column(Float, nullable=False, default=0.25)
    status = Column(String(32), nullable=False, default="DRAFT")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class InnovationValidationModel(Base):
    __tablename__ = "venture_validations"

    id = Column(String(64), primary_key=True)
    opportunity_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    validation_method = Column(String(64), nullable=False)
    evidence_summary = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.85)
    unresolved_assumptions_json = Column(Text, nullable=False, default="[]")
    validated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureExperimentModel(Base):
    __tablename__ = "venture_experiments"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    hypothesis = Column(Text, nullable=False)
    control_config_json = Column(Text, nullable=False, default="{}")
    treatment_config_json = Column(Text, nullable=False, default="{}")
    duration_days = Column(Integer, nullable=False, default=7)
    metrics_json = Column(Text, nullable=False, default="{}")
    success_criteria_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="SCHEDULED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class InnovationReviewModel(Base):
    __tablename__ = "innovation_reviews"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    strategic_fit_score = Column(Float, nullable=False, default=0.85)
    customer_value_score = Column(Float, nullable=False, default=0.90)
    technical_feasibility_score = Column(Float, nullable=False, default=0.80)
    economic_viability_score = Column(Float, nullable=False, default=0.75)
    risk_score = Column(Float, nullable=False, default=0.30)
    overall_score = Column(Float, nullable=False, default=0.82)
    recommendation = Column(String(64), nullable=False, default="PROCEED_TO_GOVERNANCE")
    reviewed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureProposalModel(Base):
    __tablename__ = "venture_proposals"

    id = Column(String(64), primary_key=True)
    opportunity_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    venture_type = Column(String(32), nullable=False, default="NEW_COMPANY")
    business_case_id = Column(String(64), nullable=False)
    required_budget_usd = Column(Integer, nullable=False, default=15000000)
    required_workforce_count = Column(Integer, nullable=False, default=4)
    risk_level = Column(String(32), nullable=False, default="MEDIUM")
    status = Column(String(32), nullable=False, default="PROPOSED")
    governance_required = Column(Boolean, nullable=False, default=True)
    governance_approval_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureInitializationPlanModel(Base):
    __tablename__ = "venture_initialization_plans"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    target_structure = Column(String(32), nullable=False, default="NEW_COMPANY")
    departments_json = Column(Text, nullable=False, default="[]")
    workforce_plan_json = Column(Text, nullable=False, default="{}")
    product_config_json = Column(Text, nullable=False, default="{}")
    financial_setup_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureResourceRequestModel(Base):
    __tablename__ = "venture_resource_requests"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    workforce_count = Column(Integer, nullable=False, default=3)
    model_budget_usd = Column(Integer, nullable=False, default=500000)
    storage_gb = Column(Integer, nullable=False, default=100)
    compute_cores = Column(Integer, nullable=False, default=16)
    status = Column(String(32), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureLaunchReadinessModel(Base):
    __tablename__ = "venture_launch_readiness_records"

    id = Column(String(64), primary_key=True)
    proposal_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    product_ready = Column(Boolean, nullable=False, default=False)
    technical_ready = Column(Boolean, nullable=False, default=False)
    security_ready = Column(Boolean, nullable=False, default=False)
    financial_ready = Column(Boolean, nullable=False, default=False)
    governance_ready = Column(Boolean, nullable=False, default=False)
    status = Column(String(32), nullable=False, default="NOT_READY")
    checked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VentureOutcomeModel(Base):
    __tablename__ = "venture_outcomes"

    id = Column(String(64), primary_key=True)
    venture_id = Column(String(64), nullable=False)
    company_id = Column(String(64), nullable=False, index=True)
    expected_outcomes_json = Column(Text, nullable=False, default="{}")
    actual_outcomes_json = Column(Text, nullable=False, default="{}")
    variance_analysis_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="INITIAL")
    measured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
