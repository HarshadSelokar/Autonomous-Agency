"""
Employee Domain Entity and Lifecycle State Machine.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import EmployeeValidationError, InvalidStateTransitionError


class SkillProficiency(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class EmployeeSkill:
    name: str
    category: str = "general"
    proficiency: SkillProficiency = SkillProficiency.INTERMEDIATE


@dataclass(frozen=True)
class EmployeeCapability:
    name: str
    description: str = ""


class EmployeeStatus(str, Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


MANAGER_CAPABILITIES: set[str] = {
    "objective_analysis",
    "planning",
    "task_decomposition",
    "employee_selection",
    "task_assignment",
    "progress_monitoring",
    "result_review",
    "blocker_resolution",
    "escalation",
    "replanning",
    "decision_making",
    "people_management",
    "project_management",
}


VALID_EMPLOYEE_TRANSITIONS: dict[EmployeeStatus, set[EmployeeStatus]] = {
    EmployeeStatus.INACTIVE: {EmployeeStatus.ACTIVE, EmployeeStatus.TERMINATED},
    EmployeeStatus.ACTIVE: {
        EmployeeStatus.ON_LEAVE,
        EmployeeStatus.SUSPENDED,
        EmployeeStatus.INACTIVE,
        EmployeeStatus.TERMINATED,
    },
    EmployeeStatus.ON_LEAVE: {
        EmployeeStatus.ACTIVE,
        EmployeeStatus.SUSPENDED,
        EmployeeStatus.TERMINATED,
    },
    EmployeeStatus.SUSPENDED: {EmployeeStatus.ACTIVE, EmployeeStatus.TERMINATED},
    EmployeeStatus.TERMINATED: set(),
}


@dataclass
class Employee:
    id: str
    employee_code: str
    name: str
    title: str
    role: str
    agent_id: str
    department_id: str | None = None
    manager_id: str | None = None
    responsibilities: list[str] = field(default_factory=list)
    skills: list[EmployeeSkill] = field(default_factory=list)
    capabilities: list[EmployeeCapability] = field(default_factory=list)
    status: EmployeeStatus = EmployeeStatus.INACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate employee business invariants."""
        if not self.id:
            raise EmployeeValidationError("Employee ID cannot be empty.")
        if not self.employee_code:
            raise EmployeeValidationError("Employee code cannot be empty.")
        if not self.name:
            raise EmployeeValidationError("Employee name cannot be empty.")
        if not self.role:
            raise EmployeeValidationError("Employee role cannot be empty.")
        if not self.agent_id:
            raise EmployeeValidationError("Employee must reference an associated Agent ID.")
        if self.manager_id and self.manager_id == self.id:
            raise EmployeeValidationError(
                f"Employee '{self.id}' cannot be assigned as their own manager."
            )

    def can_transition_to(self, target_status: EmployeeStatus) -> bool:
        """Check if transition to target_status is valid."""
        allowed = VALID_EMPLOYEE_TRANSITIONS.get(self.status, set())
        return target_status in allowed

    def transition_to(self, target_status: EmployeeStatus) -> None:
        """
        Transition employee status to target_status if valid.
        Raises InvalidStateTransitionError on invalid transition.
        """
        if self.status == target_status:
            return  # No-op

        if not self.can_transition_to(target_status):
            raise InvalidStateTransitionError(
                entity="Employee",
                entity_id=self.id,
                current_state=self.status.value,
                target_state=target_status.value,
            )

        self.status = target_status
        self.updated_at = datetime.now(UTC)

    def is_executable(self) -> bool:
        """Check if employee is in an active state allowed to execute work."""
        return self.status == EmployeeStatus.ACTIVE

    def possesses_capability(self, capability_name: str) -> bool:
        """Check if employee possesses a specific capability or skill."""
        cap_lower = capability_name.lower()
        has_cap = any(c.name.lower() == cap_lower for c in self.capabilities)
        has_skill = any(s.name.lower() == cap_lower for s in self.skills)
        return has_cap or has_skill

    def is_manager(self) -> bool:
        """
        Check if employee has managerial authority based on role, title, or manager capabilities.
        """
        role_title = f"{self.role} {self.title}".lower()
        mgr_keywords = {
            "manager",
            "director",
            "head",
            "lead",
            "chief",
            "cto",
            "ceo",
            "cpo",
            "vp",
        }
        if any(k in role_title for k in mgr_keywords):
            return True

        return any(c.name.lower() in MANAGER_CAPABILITIES for c in self.capabilities)
