"""
Product, Customer & Go-to-Market (GTM) Domain Models for Autonomous AI Organization Platform (Phase 24).

Defines core product, CRM, sales, support, customer success, marketing, and GTM analytics entities,
lifecycle state machines, and governed commercial boundaries.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.business import Money
from src.domain.exceptions import PricingPolicyViolationError, UnauthorizedCommercialCommitmentError


class ProductLifecycle(str, Enum):
    IDEA = "IDEA"
    DISCOVERY = "DISCOVERY"
    PLANNING = "PLANNING"
    DEVELOPMENT = "DEVELOPMENT"
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class CustomerLifecycleState(str, Enum):
    PROSPECT = "PROSPECT"
    QUALIFIED = "QUALIFIED"
    CUSTOMER = "CUSTOMER"
    ONBOARDING = "ONBOARDING"
    ACTIVE = "ACTIVE"
    AT_RISK = "AT_RISK"
    CHURNED = "CHURNED"


class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    CONVERTED = "CONVERTED"


class OpportunityStage(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    QUALIFIED = "QUALIFIED"
    DISCOVERY = "DISCOVERY"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SupportCaseStatus(str, Enum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_CUSTOMER = "WAITING_CUSTOMER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SupportPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FeedbackCategory(str, Enum):
    FEATURE_REQUEST = "FEATURE_REQUEST"
    BUG_REPORT = "BUG_REPORT"
    USABILITY = "USABILITY"
    PRICING = "PRICING"
    PERFORMANCE = "PERFORMANCE"
    GENERAL = "GENERAL"


# --- Product Entities ---

@dataclass
class Product:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    code: str = ""
    description: str = ""
    category: str = "SOFTWARE"
    lifecycle: ProductLifecycle = ProductLifecycle.ACTIVE
    owner_employee_id: str = ""
    target_market: str = "ENTERPRISE"
    base_price_cents: int = 0
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def money_base_price(self) -> Money:
        return Money(self.base_price_cents, self.currency)


@dataclass
class ProductVersion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = ""
    version_string: str = "1.0.0"
    release_notes: str = ""
    is_released: bool = False
    release_date: Optional[datetime] = None


@dataclass
class ProductRoadmap:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = ""
    title: str = ""
    target_period: str = "Q4-2026"
    objectives_json: List[str] = field(default_factory=list)
    priorities_json: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProductRequirement:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = ""
    title: str = ""
    user_story: str = ""
    priority: str = "MEDIUM"
    source_feedback_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "PROPOSED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ProductFeedback:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str = ""
    customer_id: str = ""
    category: FeedbackCategory = FeedbackCategory.FEATURE_REQUEST
    summary: str = ""
    raw_content: str = ""
    importance_score: int = 5
    validated_insight: Optional[str] = None
    status: str = "RECEIVED"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# --- Customer Entities ---

@dataclass
class Customer:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: str = ""
    segment: str = "ENTERPRISE"
    lifecycle_state: CustomerLifecycleState = CustomerLifecycleState.PROSPECT
    account_manager_id: Optional[str] = None
    health_score: float = 100.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerContact:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    name: str = ""
    email: str = ""
    role: str = ""
    is_primary: bool = False


@dataclass
class CustomerInteraction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    contact_id: Optional[str] = None
    interaction_type: str = "EMAIL"
    channel: str = "EXTERNAL_CUSTOMER"
    summary: str = ""
    actor_id: str = "SYSTEM"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    provenance_reference: Optional[str] = None


@dataclass
class CustomerHealthSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    health_score: float = 100.0
    product_usage_rate: float = 0.0
    open_support_cases: int = 0
    satisfaction_score: float = 5.0
    status: str = "HEALTHY"
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CustomerOutcome:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    goal_description: str = ""
    measured_outcome: str = ""
    verified_status: str = "UNVERIFIED"
    achieved_at: Optional[datetime] = None


# --- Sales & Commercial Entities ---

@dataclass
class Lead:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    contact_name: str = ""
    contact_email: str = ""
    source: str = "INBOUND_WEB"
    status: LeadStatus = LeadStatus.NEW
    score: int = 0
    assigned_owner_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Opportunity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    title: str = ""
    product_id: str = ""
    stage: OpportunityStage = OpportunityStage.IDENTIFIED
    estimated_value_cents: int = 0
    currency: str = "USD"
    probability_pct: int = 20
    owner_id: str = ""
    expected_close_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SalesActivity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    activity_type: str = "QUALIFICATION_CALL"
    summary: str = ""
    performed_by: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Proposal:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    opportunity_id: str = ""
    title: str = ""
    product_id: str = ""
    base_amount_cents: int = 0
    discount_pct: float = 0.0
    total_amount_cents: int = 0
    currency: str = "USD"
    status: ProposalStatus = ProposalStatus.DRAFT
    governance_approval_id: Optional[str] = None
    owner_id: str = ""
    valid_until: datetime = field(default_factory=lambda: datetime.now(UTC))

    def calculate_total(self) -> int:
        if self.discount_pct < 0.0 or self.discount_pct > 100.0:
            raise PricingPolicyViolationError(self.discount_pct, 15.0)
        discount_amount = round(self.base_amount_cents * (self.discount_pct / 100.0))
        self.total_amount_cents = max(0, self.base_amount_cents - discount_amount)
        return self.total_amount_cents


# --- Customer Success & Support Entities ---

@dataclass
class CustomerOnboardingPlan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    order_id: Optional[str] = None
    milestones_json: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "IN_PROGRESS"
    completion_pct: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SupportCase:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    subject: str = ""
    description: str = ""
    priority: SupportPriority = SupportPriority.MEDIUM
    status: SupportCaseStatus = SupportCaseStatus.OPEN
    assigned_employee_id: Optional[str] = None
    escalated_task_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# --- Marketing & GTM Entities ---

@dataclass
class MarketingCampaign:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    objective: str = ""
    target_audience: str = ""
    channel: str = "EMAIL"
    budget_cents: int = 0
    spent_cents: int = 0
    currency: str = "USD"
    status: CampaignStatus = CampaignStatus.DRAFT
    governance_approval_id: Optional[str] = None
    owner_id: str = ""
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


@dataclass
class MarketingAsset:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str = ""
    title: str = ""
    asset_type: str = "COPY_TEXT"
    content_payload: str = ""
    review_status: str = "PENDING_REVIEW"


@dataclass
class CommunicationPreference:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    contact_email: str = ""
    opt_in_marketing: bool = True
    opt_in_product_updates: bool = True
    opt_out_all: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class GTMMetric:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    metric_value: float = 0.0
    unit: str = "COUNT"
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
