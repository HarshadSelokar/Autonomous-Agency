"""
Tenant Domain Entity, Value Objects, and State Machines for Phase 32 Multi-Tenancy Foundation.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import InvalidStateTransitionError


class TenantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class TenantPlan(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


# Valid state transitions for tenant status
VALID_TENANT_TRANSITIONS: dict[TenantStatus, set[TenantStatus]] = {
    TenantStatus.ACTIVE: {TenantStatus.SUSPENDED, TenantStatus.DELETED},
    TenantStatus.SUSPENDED: {TenantStatus.ACTIVE, TenantStatus.DELETED},
    TenantStatus.DELETED: set(),  # Terminal state
}


@dataclass(frozen=True)
class TenantConfiguration:
    max_users: int = 100
    max_projects: int = 50
    max_workflows: int = 20
    allowed_providers: list[str] = field(default_factory=lambda: ["groq", "fake"])
    custom_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class Tenant:
    id: str
    name: str
    slug: str
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    configuration: TenantConfiguration = field(default_factory=TenantConfiguration)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def transition_to(self, target_status: TenantStatus) -> None:
        valid = VALID_TENANT_TRANSITIONS.get(self.status, set())
        if target_status not in valid:
            raise InvalidStateTransitionError(
                entity="Tenant",
                entity_id=self.id,
                current_state=str(self.status),
                target_state=str(target_status),
            )
        self.status = target_status
        self.updated_at = datetime.now(UTC)

    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE
