"""
Human Governance Domain Entities and Value Objects for Phase 11.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AutonomyLevel(str, Enum):
    FULLY_AUTONOMOUS = "FULLY_AUTONOMOUS"
    SUPERVISED = "SUPERVISED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    HUMAN_ONLY = "HUMAN_ONLY"
    BLOCKED = "BLOCKED"


class GovernanceScope(str, Enum):
    GLOBAL = "GLOBAL"
    COMPANY = "COMPANY"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"
    EMPLOYEE = "EMPLOYEE"
    AGENT = "AGENT"
    TASK = "TASK"
    TOOL = "TOOL"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ViolationCategory(str, Enum):
    UNAUTHORIZED_ACTION = "UNAUTHORIZED_ACTION"
    APPROVAL_BYPASS = "APPROVAL_BYPASS"
    FORBIDDEN_TOOL = "FORBIDDEN_TOOL"
    EXCESSIVE_AUTONOMY = "EXCESSIVE_AUTONOMY"
    SECURITY_POLICY_VIOLATION = "SECURITY_POLICY_VIOLATION"
    DATA_ACCESS_VIOLATION = "DATA_ACCESS_VIOLATION"
    SEPARATION_OF_DUTIES_VIOLATION = "SEPARATION_OF_DUTIES_VIOLATION"
    STALE_APPROVAL = "STALE_APPROVAL"
    INVALID_OVERRIDE = "INVALID_OVERRIDE"


@dataclass
class GovernanceRule:
    """Defines a specific rule within a governance policy."""
    rule_id: str
    name: str
    description: str
    scope: GovernanceScope
    target_pattern: str                       # e.g., "tool:deploy*", "action:financial*", "workspace:prod*"
    min_risk_level: RiskLevel = RiskLevel.MEDIUM
    autonomy_level: AutonomyLevel = AutonomyLevel.APPROVAL_REQUIRED
    required_approver_roles: List[str] = field(default_factory=list)
    prohibit_self_approval: bool = True
    approval_validity_seconds: int = 3600
    allow_override: bool = True


@dataclass
class GovernancePolicy:
    """Represents a policy at a specific hierarchy level."""
    policy_id: str
    name: str
    scope: GovernanceScope
    scope_id: Optional[str] = None           # e.g., dept_id, project_id, employee_id
    level: str = "COMPANY"                   # "SYSTEM", "COMPANY", "DEPARTMENT", "PROJECT", "TASK"
    rules: List[GovernanceRule] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def precedence_order(self) -> int:
        order = {"SYSTEM": 5, "COMPANY": 4, "DEPARTMENT": 3, "PROJECT": 2, "TASK": 1}
        return order.get(self.level, 0)


@dataclass
class GovernanceApprovalRequest:
    """Represents a human approval request for a governed action."""
    request_id: str
    action_type: str                         # e.g., "TOOL_EXECUTION", "DEPLOYMENT", "FINANCIAL_TRANSFER"
    action_target: str
    requested_by_actor_id: str               # Employee or Agent ID requesting
    requested_by_employee_id: Optional[str] = None
    requested_by_agent_id: Optional[str] = None
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.HIGH
    status: ApprovalStatus = ApprovalStatus.PENDING
    required_approver_roles: List[str] = field(default_factory=list)
    prohibit_self_approval: bool = True
    approved_by_actor_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class HumanIntervention:
    """Records a human intervention action during autonomous execution."""
    intervention_id: str
    intervention_type: str                  # "PAUSE", "RESUME", "REJECT", "OVERRIDE", "CANCEL", "REWORK"
    scope: GovernanceScope
    scope_id: str
    actor_id: str
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EmergencyStopState:
    """Tracks active emergency stops (kill switch)."""
    stop_id: str
    scope: GovernanceScope
    scope_id: str
    activated_by_actor_id: str
    reason: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GovernanceOverride:
    """Records an audited human override of a governance decision."""
    override_id: str
    action_id: str
    policy_id: str
    actor_id: str
    reason: str
    previous_autonomy_level: AutonomyLevel
    override_autonomy_level: AutonomyLevel
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PolicyViolation:
    """Records a detected governance policy violation."""
    violation_id: str
    category: ViolationCategory
    summary: str
    actor_id: str
    task_id: Optional[str] = None
    policy_id: Optional[str] = None
    severity: RiskLevel = RiskLevel.HIGH
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
