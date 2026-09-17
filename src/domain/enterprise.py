"""
Domain models for Phase 29 Enterprise-Scale Autonomous Company Platform, Federation & Operations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, UTC
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class EnterpriseLifecycle(str, Enum):
    PROPOSED = "PROPOSED"
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    RESTRUCTURING = "RESTRUCTURING"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class NodeType(str, Enum):
    ENTERPRISE = "ENTERPRISE"
    COMPANY = "COMPANY"
    SUBSIDIARY = "SUBSIDIARY"
    BUSINESS_UNIT = "BUSINESS_UNIT"
    REGION = "REGION"
    DEPARTMENT = "DEPARTMENT"
    TEAM = "TEAM"
    SHARED_SERVICE = "SHARED_SERVICE"
    PROJECT_GROUP = "PROJECT_GROUP"


class RelationshipType(str, Enum):
    PARENT_CHILD = "PARENT_CHILD"
    OWNERSHIP = "OWNERSHIP"
    OPERATIONAL = "OPERATIONAL"
    SERVICE = "SERVICE"
    REPORTING = "REPORTING"
    DEPENDENCY = "DEPENDENCY"
    PORTFOLIO = "PORTFOLIO"


class ServiceType(str, Enum):
    FINANCE = "FINANCE"
    HR = "HR"
    LEGAL = "LEGAL"
    SECURITY = "SECURITY"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    DATA_PLATFORM = "DATA_PLATFORM"
    AI_PLATFORM = "AI_PLATFORM"
    ENGINEERING_PLATFORM = "ENGINEERING_PLATFORM"
    CUSTOMER_SUPPORT_PLATFORM = "CUSTOMER_SUPPORT_PLATFORM"
    PROCUREMENT = "PROCUREMENT"
    RESEARCH_PLATFORM = "RESEARCH_PLATFORM"
    INTERNAL_COMMUNICATIONS = "INTERNAL_COMMUNICATIONS"


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    HIGHLY_RESTRICTED = "HIGHLY_RESTRICTED"


class InterCompanyRequestStatus(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class PortfolioCategory(str, Enum):
    COMPANY = "COMPANY"
    SUBSIDIARY = "SUBSIDIARY"
    PRODUCT = "PRODUCT"
    INITIATIVE = "INITIATIVE"
    RESEARCH_PROGRAM = "RESEARCH_PROGRAM"
    INNOVATION_VENTURE = "INNOVATION_VENTURE"
    BUSINESS_UNIT = "BUSINESS_UNIT"


class PortfolioPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    EXPERIMENTAL = "EXPERIMENTAL"


class ObjectiveScope(str, Enum):
    ENTERPRISE = "ENTERPRISE"
    COMPANY = "COMPANY"
    BUSINESS_UNIT = "BUSINESS_UNIT"
    DEPARTMENT = "DEPARTMENT"
    TEAM = "TEAM"


@dataclass
class EnterpriseProfile:
    industry: str = "GLOBAL_TECHNOLOGY_ENTERPRISE"
    headquarters_region: str = "NORTH_AMERICA"
    operating_currency: str = "USD"
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Enterprise:
    id: str = field(default_factory=lambda: f"ent-{uuid.uuid4().hex[:8]}")
    name: str = ""
    code: str = ""
    status: EnterpriseLifecycle = EnterpriseLifecycle.PROPOSED
    profile: EnterpriseProfile = field(default_factory=EnterpriseProfile)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseOrganizationNode:
    id: str = field(default_factory=lambda: f"node-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    name: str = ""
    node_type: NodeType = NodeType.COMPANY
    reference_id: Optional[str] = None  # e.g., company_id, department_id
    parent_node_id: Optional[str] = None
    region: str = "GLOBAL"
    data_classification: DataClassification = DataClassification.INTERNAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseRelationship:
    id: str = field(default_factory=lambda: f"rel-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    relationship_type: RelationshipType = RelationshipType.PARENT_CHILD
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseService:
    id: str = field(default_factory=lambda: f"svc-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    owner_node_id: str = ""
    name: str = ""
    service_type: ServiceType = ServiceType.INFRASTRUCTURE
    capacity_units: int = 100
    available_units: int = 100
    sla_description: str = "99.9% availability"
    governance_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseServiceAgreement:
    id: str = field(default_factory=lambda: f"sla-{uuid.uuid4().hex[:8]}")
    service_id: str = ""
    consumer_node_id: str = ""
    allocated_units: int = 10
    cost_allocation_usd: float = 0.0
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PortfolioItem:
    id: str = field(default_factory=lambda: f"pitem-{uuid.uuid4().hex[:8]}")
    portfolio_id: str = ""
    name: str = ""
    category: PortfolioCategory = PortfolioCategory.COMPANY
    reference_id: str = ""
    priority: PortfolioPriority = PortfolioPriority.MEDIUM
    allocated_budget_usd: float = 0.0
    expected_roi: float = 0.20
    health_score: float = 1.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterprisePortfolio:
    id: str = field(default_factory=lambda: f"port-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    name: str = ""
    description: str = ""
    total_budget_usd: float = 0.0
    items: List[PortfolioItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseObjective:
    id: str = field(default_factory=lambda: f"eobj-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    title: str = ""
    description: str = ""
    target_metric: str = ""
    target_value: float = 100.0
    current_value: float = 0.0
    scope: ObjectiveScope = ObjectiveScope.ENTERPRISE
    owner_node_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ObjectiveCascade:
    id: str = field(default_factory=lambda: f"casc-{uuid.uuid4().hex[:8]}")
    parent_objective_id: str = ""
    child_objective_id: str = ""
    child_node_id: str = ""
    contribution_weight: float = 1.0
    alignment_status: str = "ALIGNED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterprisePolicyProfile:
    id: str = field(default_factory=lambda: f"epol-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    node_id: str = ""
    mandatory_security_level: str = "HIGH"
    max_single_budget_spend_usd: float = 50000.0
    prohibited_external_actions: List[str] = field(default_factory=lambda: ["DIRECT_LEGAL_CONTRACT", "UNAPPROVED_PAYMENT"])
    require_human_governance: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AuthorityGrant:
    id: str = field(default_factory=lambda: f"auth-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    grantor_node_id: str = ""
    grantee_node_id: str = ""
    scope: str = ""
    action: str = ""
    max_impact_usd: float = 100000.0
    expires_at: Optional[datetime] = None
    is_revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseResourcePool:
    id: str = field(default_factory=lambda: f"pool-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    name: str = ""
    resource_type: str = "COMPUTE"
    total_capacity: float = 1000.0
    available_capacity: float = 1000.0
    unit: str = "UNITS"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ResourceAllocation:
    id: str = field(default_factory=lambda: f"alloc-{uuid.uuid4().hex[:8]}")
    pool_id: str = ""
    consumer_node_id: str = ""
    allocated_amount: float = 50.0
    status: str = "ALLOCATED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseCapacitySnapshot:
    id: str = field(default_factory=lambda: f"capsnap-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    total_agent_execution_capacity: int = 100
    used_agent_execution_capacity: int = 20
    shared_service_utilization_pct: float = 45.0
    capacity_gap_identified: bool = False
    snapshot_time: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InterCompanyRequest:
    id: str = field(default_factory=lambda: f"icreq-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    source_company_id: str = ""
    destination_company_id: str = ""
    requester_id: str = ""
    requested_capability: str = ""
    purpose: str = ""
    status: InterCompanyRequestStatus = InterCompanyRequestStatus.PENDING
    governance_approval_id: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseDependency:
    id: str = field(default_factory=lambda: f"dep-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    dependent_node_id: str = ""
    provider_node_id: str = ""
    dependency_type: str = "SERVICE"
    criticality: str = "HIGH"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseHealthSnapshot:
    id: str = field(default_factory=lambda: f"ehealth-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    objective_health_score: float = 0.90
    workforce_capacity_score: float = 0.85
    financial_health_score: float = 0.95
    infrastructure_health_score: float = 0.99
    governance_compliance_score: float = 1.00
    overall_health_score: float = 0.938
    health_signals: Dict[str, Any] = field(default_factory=dict)
    snapshot_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseRisk:
    id: str = field(default_factory=lambda: f"erisk-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    title: str = ""
    description: str = ""
    impact_usd: float = 500000.0
    probability: float = 0.25
    owner_node_id: Optional[str] = None
    status: str = "OPEN"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseOpportunity:
    id: str = field(default_factory=lambda: f"eopp-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    title: str = ""
    description: str = ""
    potential_value_usd: float = 2000000.0
    confidence: float = 0.80
    status: str = "IDENTIFIED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseKnowledgeSharingPolicy:
    id: str = field(default_factory=lambda: f"kpol-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    source_company_id: str = ""
    target_company_id: str = ""
    allowed_classifications: List[DataClassification] = field(default_factory=lambda: [DataClassification.PUBLIC, DataClassification.INTERNAL])
    governance_approved: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EnterpriseLearnedPropagation:
    id: str = field(default_factory=lambda: f"lprop-{uuid.uuid4().hex[:8]}")
    enterprise_id: str = ""
    source_company_id: str = ""
    learning_candidate_id: str = ""
    lesson_summary: str = ""
    applicability_conditions: str = ""
    governance_approval_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
