"""
SQLAlchemy ORM models for Phase 24 Product, Customer & GTM Operations.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON

from src.infrastructure.database import Base


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, default="SOFTWARE")
    lifecycle = Column(String(50), nullable=False, default="ACTIVE")
    owner_employee_id = Column(String(36), nullable=False)
    target_market = Column(String(100), nullable=False, default="ENTERPRISE")
    base_price_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ProductVersionModel(Base):
    __tablename__ = "product_versions"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), nullable=False, index=True)
    version_string = Column(String(50), nullable=False)
    release_notes = Column(Text, nullable=False)
    is_released = Column(Boolean, nullable=False, default=False)
    release_date = Column(DateTime(timezone=True), nullable=True)


class ProductRoadmapModel(Base):
    __tablename__ = "product_roadmaps"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    target_period = Column(String(50), nullable=False)
    objectives_json = Column(JSON, nullable=True)
    priorities_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ProductRequirementModel(Base):
    __tablename__ = "product_requirements"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    user_story = Column(Text, nullable=False)
    priority = Column(String(50), nullable=False, default="MEDIUM")
    source_feedback_id = Column(String(36), nullable=True)
    task_id = Column(String(36), nullable=True)
    status = Column(String(50), nullable=False, default="PROPOSED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ProductFeedbackModel(Base):
    __tablename__ = "product_feedback"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="FEATURE_REQUEST")
    summary = Column(String(255), nullable=False)
    raw_content = Column(Text, nullable=False)
    importance_score = Column(Integer, nullable=False, default=5)
    validated_insight = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="RECEIVED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    segment = Column(String(100), nullable=False, default="ENTERPRISE")
    lifecycle_state = Column(String(50), nullable=False, default="PROSPECT")
    account_manager_id = Column(String(36), nullable=True)
    health_score = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class CustomerContactModel(Base):
    __tablename__ = "customer_contacts"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)


class CustomerInteractionModel(Base):
    __tablename__ = "customer_interactions"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    contact_id = Column(String(36), nullable=True)
    interaction_type = Column(String(50), nullable=False, default="EMAIL")
    channel = Column(String(50), nullable=False, default="EXTERNAL_CUSTOMER")
    summary = Column(Text, nullable=False)
    actor_id = Column(String(36), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    provenance_reference = Column(Text, nullable=True)


class CustomerHealthSnapshotModel(Base):
    __tablename__ = "customer_health_snapshots"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    health_score = Column(Float, nullable=False, default=100.0)
    product_usage_rate = Column(Float, nullable=False, default=0.0)
    open_support_cases = Column(Integer, nullable=False, default=0)
    satisfaction_score = Column(Float, nullable=False, default=5.0)
    status = Column(String(50), nullable=False, default="HEALTHY")
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CustomerOutcomeModel(Base):
    __tablename__ = "customer_outcomes"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    goal_description = Column(Text, nullable=False)
    measured_outcome = Column(Text, nullable=False)
    verified_status = Column(String(50), nullable=False, default="UNVERIFIED")
    achieved_at = Column(DateTime(timezone=True), nullable=True)


class LeadModel(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False, default="INBOUND_WEB")
    status = Column(String(50), nullable=False, default="NEW")
    score = Column(Integer, nullable=False, default=0)
    assigned_owner_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class OpportunityModel(Base):
    __tablename__ = "opportunities"

    id = Column(String(36), primary_key=True)
    lead_id = Column(String(36), nullable=True)
    customer_id = Column(String(36), nullable=True)
    title = Column(String(255), nullable=False)
    product_id = Column(String(36), nullable=False)
    stage = Column(String(50), nullable=False, default="IDENTIFIED")
    estimated_value_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    probability_pct = Column(Integer, nullable=False, default=20)
    owner_id = Column(String(36), nullable=False)
    expected_close_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SalesActivityModel(Base):
    __tablename__ = "sales_activities"

    id = Column(String(36), primary_key=True)
    opportunity_id = Column(String(36), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    performed_by = Column(String(36), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ProposalModel(Base):
    __tablename__ = "proposals"

    id = Column(String(36), primary_key=True)
    opportunity_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    product_id = Column(String(36), nullable=False)
    base_amount_cents = Column(BigInteger, nullable=False, default=0)
    discount_pct = Column(Float, nullable=False, default=0.0)
    total_amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="DRAFT")
    governance_approval_id = Column(String(36), nullable=True)
    owner_id = Column(String(36), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class CustomerOnboardingPlanModel(Base):
    __tablename__ = "customer_onboarding_plans"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=True)
    milestones_json = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="IN_PROGRESS")
    completion_pct = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SupportCaseModel(Base):
    __tablename__ = "support_cases"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), nullable=False, default="MEDIUM")
    status = Column(String(50), nullable=False, default="OPEN")
    assigned_employee_id = Column(String(36), nullable=True)
    escalated_task_id = Column(String(36), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class MarketingCampaignModel(Base):
    __tablename__ = "marketing_campaigns"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    target_audience = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False, default="EMAIL")
    budget_cents = Column(BigInteger, nullable=False, default=0)
    spent_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="DRAFT")
    governance_approval_id = Column(String(36), nullable=True)
    owner_id = Column(String(36), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)


class MarketingAssetModel(Base):
    __tablename__ = "marketing_assets"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False, default="COPY_TEXT")
    content_payload = Column(Text, nullable=False)
    review_status = Column(String(50), nullable=False, default="PENDING_REVIEW")


class CommunicationPreferenceModel(Base):
    __tablename__ = "communication_preferences"

    id = Column(String(36), primary_key=True)
    contact_email = Column(String(255), nullable=False, index=True)
    opt_in_marketing = Column(Boolean, nullable=False, default=True)
    opt_in_product_updates = Column(Boolean, nullable=False, default=True)
    opt_out_all = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class GTMMetricModel(Base):
    __tablename__ = "gtm_metrics"

    id = Column(String(36), primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False, default="COUNT")
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
