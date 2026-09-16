"""Department Domain Entity and Enums for Phase 14 Enterprise Department Expansion.

Represents an organizational boundary operating on the Company OS.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class DepartmentStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class DepartmentHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    AT_RISK = "AT_RISK"
    PAUSED = "PAUSED"


class DepartmentPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class DepartmentCapability:
    name: str
    category: str
    description: str = ""


@dataclass
class DepartmentResponsibility:
    title: str
    description: str
    capability_names: list[str] = field(default_factory=list)


@dataclass
class Department:
    id: str
    name: str
    code: str
    description: str = ""
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    purpose: str = ""
    manager_employee_id: str | None = None
    parent_department_id: str | None = None
    capabilities: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    policies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
