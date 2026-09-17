"""
SQLAlchemy ORM models for Phase 29 Enterprise OS.
"""

from datetime import datetime, timezone, UTC
from typing import Any
import json

from sqlalchemy import (
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


class EnterpriseModel(Base):
    __tablename__ = "enterprises"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(String(64), nullable=False, default="PROPOSED", index=True)
    profile_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    nodes = relationship("EnterpriseOrganizationNodeModel", back_populates="enterprise", cascade="all, delete-orphan")


class EnterpriseOrganizationNodeModel(Base):
    __tablename__ = "enterprise_topology_nodes"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    node_type = Column(String(64), nullable=False, index=True)
    reference_id = Column(String(64), nullable=True)
    parent_node_id = Column(String(64), ForeignKey("enterprise_topology_nodes.id", ondelete="SET NULL"), nullable=True)
    region = Column(String(64), nullable=False, default="GLOBAL")
    data_classification = Column(String(64), nullable=False, default="INTERNAL")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    enterprise = relationship("EnterpriseModel", back_populates="nodes")


class EnterpriseRelationshipModel(Base):
    __tablename__ = "enterprise_relationships"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(String(64), ForeignKey("enterprise_topology_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(String(64), ForeignKey("enterprise_topology_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False, default="")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterpriseServiceModel(Base):
    __tablename__ = "enterprise_services"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_node_id = Column(String(64), ForeignKey("enterprise_topology_nodes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    service_type = Column(String(64), nullable=False)
    capacity_units = Column(Integer, nullable=False, default=100)
    available_units = Column(Integer, nullable=False, default=100)
    sla_description = Column(Text, nullable=False, default="")
    governance_required = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterpriseServiceAgreementModel(Base):
    __tablename__ = "enterprise_service_agreements"

    id = Column(String(64), primary_key=True)
    service_id = Column(String(64), ForeignKey("enterprise_services.id", ondelete="CASCADE"), nullable=False, index=True)
    consumer_node_id = Column(String(64), ForeignKey("enterprise_topology_nodes.id", ondelete="CASCADE"), nullable=False)
    allocated_units = Column(Integer, nullable=False, default=10)
    cost_allocation_usd = Column(Float, nullable=False, default=0.0)
    status = Column(String(64), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterprisePortfolioModel(Base):
    __tablename__ = "enterprise_portfolios"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    total_budget_usd = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterprisePortfolioItemModel(Base):
    __tablename__ = "enterprise_portfolio_items"

    id = Column(String(64), primary_key=True)
    portfolio_id = Column(String(64), ForeignKey("enterprise_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)
    reference_id = Column(String(64), nullable=False)
    priority = Column(String(64), nullable=False, default="MEDIUM")
    allocated_budget_usd = Column(Float, nullable=False, default=0.0)
    expected_roi = Column(Float, nullable=False, default=0.20)
    health_score = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterpriseObjectiveModel(Base):
    __tablename__ = "enterprise_objectives"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    target_metric = Column(String(128), nullable=False, default="")
    target_value = Column(Float, nullable=False, default=100.0)
    current_value = Column(Float, nullable=False, default=0.0)
    scope = Column(String(64), nullable=False, default="ENTERPRISE")
    owner_node_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ObjectiveCascadeModel(Base):
    __tablename__ = "objective_cascades"

    id = Column(String(64), primary_key=True)
    parent_objective_id = Column(String(64), ForeignKey("enterprise_objectives.id", ondelete="CASCADE"), nullable=False, index=True)
    child_objective_id = Column(String(64), ForeignKey("enterprise_objectives.id", ondelete="CASCADE"), nullable=False, index=True)
    child_node_id = Column(String(64), nullable=False)
    contribution_weight = Column(Float, nullable=False, default=1.0)
    alignment_status = Column(String(64), nullable=False, default="ALIGNED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterprisePolicyProfileModel(Base):
    __tablename__ = "enterprise_policy_profiles"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False, index=True)
    mandatory_security_level = Column(String(64), nullable=False, default="HIGH")
    max_single_budget_spend_usd = Column(Float, nullable=False, default=50000.0)
    prohibited_external_actions_json = Column(Text, nullable=False, default="[]")
    require_human_governance = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AuthorityGrantModel(Base):
    __tablename__ = "enterprise_authority_grants"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    grantor_node_id = Column(String(64), nullable=False)
    grantee_node_id = Column(String(64), nullable=False)
    scope = Column(String(128), nullable=False)
    action = Column(String(128), nullable=False)
    max_impact_usd = Column(Float, nullable=False, default=100000.0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterpriseResourcePoolModel(Base):
    __tablename__ = "enterprise_resource_pools"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    resource_type = Column(String(64), nullable=False)
    total_capacity = Column(Float, nullable=False, default=1000.0)
    available_capacity = Column(Float, nullable=False, default=1000.0)
    unit = Column(String(32), nullable=False, default="UNITS")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ResourceAllocationModel(Base):
    __tablename__ = "enterprise_resource_allocations"

    id = Column(String(64), primary_key=True)
    pool_id = Column(String(64), ForeignKey("enterprise_resource_pools.id", ondelete="CASCADE"), nullable=False, index=True)
    consumer_node_id = Column(String(64), nullable=False)
    allocated_amount = Column(Float, nullable=False, default=50.0)
    status = Column(String(64), nullable=False, default="ALLOCATED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class InterCompanyRequestModel(Base):
    __tablename__ = "enterprise_intercompany_requests"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    source_company_id = Column(String(64), nullable=False, index=True)
    destination_company_id = Column(String(64), nullable=False, index=True)
    requester_id = Column(String(64), nullable=False)
    requested_capability = Column(String(255), nullable=False)
    purpose = Column(Text, nullable=False, default="")
    status = Column(String(64), nullable=False, default="PENDING")
    governance_approval_id = Column(String(64), nullable=True)
    result_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterpriseRiskModel(Base):
    __tablename__ = "enterprise_risks"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    impact_usd = Column(Float, nullable=False, default=500000.0)
    probability = Column(Float, nullable=False, default=0.25)
    owner_node_id = Column(String(64), nullable=True)
    status = Column(String(64), nullable=False, default="OPEN")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class EnterpriseOpportunityModel(Base):
    __tablename__ = "enterprise_opportunities"

    id = Column(String(64), primary_key=True)
    enterprise_id = Column(String(64), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    potential_value_usd = Column(Float, nullable=False, default=2000000.0)
    confidence = Column(Float, nullable=False, default=0.80)
    status = Column(String(64), nullable=False, default="IDENTIFIED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
