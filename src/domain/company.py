"""
Multi-Company & Multi-Tenant Organization Domain Models for Phase 25.

Defines first-class Company entity, Lifecycle state machine, Profiles, Memberships,
Templates, Governed Cross-Company Relationships, Data Share Requests, Resource Quotas,
and CompanyContext boundary objects.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.exceptions import (
    InvalidLifecycleTransitionError,
    TenantIsolationViolationError,
)


class CompanyLifecycle(str, Enum):
    PROPOSED = "PROPOSED"
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class CompanyType(str, Enum):
    AUTONOMOUS = "AUTONOMOUS"
    INTERNAL = "INTERNAL"
    SANDBOX = "SANDBOX"
    SIMULATION = "SIMULATION"
    EXPERIMENTAL = "EXPERIMENTAL"


class CompanyRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    MANAGER = "MANAGER"
    VIEWER = "VIEWER"
    AUDITOR = "AUDITOR"


class RelationshipType(str, Enum):
    PARTNER = "PARTNER"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    SUBSIDIARY = "SUBSIDIARY"
    PARENT = "PARENT"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    COLLABORATOR = "COLLABORATOR"
    COMPETITOR = "COMPETITOR"
    INTERNAL = "INTERNAL"
    OTHER = "OTHER"


class DataShareScope(str, Enum):
    READ_ONLY = "READ_ONLY"
    AGGREGATED = "AGGREGATED"
    SPECIFIC_RECORD = "SPECIFIC_RECORD"
    DOCUMENT = "DOCUMENT"
    METRIC = "METRIC"
    API_RESULT = "API_RESULT"


class DataShareStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ExecutionEnvironment(str, Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    SANDBOX = "SANDBOX"
    SIMULATION = "SIMULATION"


@dataclass
class Company:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    legal_name: str = ""
    slug: str = ""
    description: str = ""
    company_type: CompanyType = CompanyType.AUTONOMOUS
    industry: str = "TECHNOLOGY"
    timezone: str = "UTC"
    locale: str = "en_US"
    currency: str = "USD"
    lifecycle: CompanyLifecycle = CompanyLifecycle.PROPOSED
    owner_id: str = "SYSTEM"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_lifecycle(self, target_lifecycle: CompanyLifecycle) -> None:
        """Enforces valid company lifecycle transitions."""
        valid_transitions = {
            CompanyLifecycle.PROPOSED: [CompanyLifecycle.INITIALIZING, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.INITIALIZING: [CompanyLifecycle.ACTIVE, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.ACTIVE: [CompanyLifecycle.PAUSED, CompanyLifecycle.SUSPENDED, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.PAUSED: [CompanyLifecycle.ACTIVE, CompanyLifecycle.SUSPENDED, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.SUSPENDED: [CompanyLifecycle.ACTIVE, CompanyLifecycle.ARCHIVED],
            CompanyLifecycle.ARCHIVED: [],  # Terminal state
        }

        allowed = valid_transitions.get(self.lifecycle, [])
        if target_lifecycle not in allowed:
            raise InvalidLifecycleTransitionError(self.id, self.lifecycle.value, target_lifecycle.value)

        self.lifecycle = target_lifecycle
        self.updated_at = datetime.now(UTC)


@dataclass
class CompanyProfile:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    operating_hours: str = "24/7"
    model_routing_policy: Dict[str, Any] = field(default_factory=dict)
    tool_policy: Dict[str, Any] = field(default_factory=dict)
    governance_defaults: Dict[str, Any] = field(default_factory=dict)
    workforce_config: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyMembership:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    user_id: str = ""
    role: CompanyRole = CompanyRole.VIEWER
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyTemplate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    industry: str = ""
    structure_json: Dict[str, Any] = field(default_factory=dict)
    default_departments: List[str] = field(default_factory=list)
    default_roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyRelationship:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_a_id: str = ""
    company_b_id: str = ""
    relationship_type: RelationshipType = RelationshipType.PARTNER
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyDataShareRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_company_id: str = ""
    target_company_id: str = ""
    data_scope: DataShareScope = DataShareScope.READ_ONLY
    purpose: str = ""
    status: DataShareStatus = DataShareStatus.REQUESTED
    governance_approval_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None


@dataclass
class CompanyResourceQuota:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    max_concurrent_tasks: int = 100
    max_concurrent_agents: int = 50
    max_monthly_model_calls: int = 100000
    max_storage_mb: int = 50000
    max_simulations: int = 10
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CompanyResourceUsage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str = ""
    active_tasks: int = 0
    active_agents: int = 0
    monthly_model_calls: int = 0
    storage_mb: int = 0
    active_simulations: int = 0
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class CompanyContext:
    company_id: str
    user_id: str = "SYSTEM"
    role: CompanyRole = CompanyRole.ADMIN
    environment: ExecutionEnvironment = ExecutionEnvironment.PRODUCTION
    simulation_id: Optional[str] = None

    def verify_company_access(self, target_company_id: str, resource_type: str = "resource") -> None:
        """Enforces tenant isolation between company contexts."""
        if self.company_id != target_company_id:
            raise TenantIsolationViolationError(self.company_id, target_company_id, resource_type)
