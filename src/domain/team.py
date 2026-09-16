"""
Team Domain Module.

Defines entities, value objects, and enums for Team management, member allocations,
team lifecycle, capabilities derivation, and health metrics.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class TeamStatus(str, Enum):
    PROPOSED = "PROPOSED"
    FORMING = "FORMING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISSOLVING = "DISSOLVING"
    DISSOLVED = "DISSOLVED"


class TeamType(str, Enum):
    PROJECT = "PROJECT"
    DEPARTMENTAL = "DEPARTMENTAL"
    CROSS_DEPARTMENT = "CROSS_DEPARTMENT"
    TEMPORARY = "TEMPORARY"
    TASK_FORCE = "TASK_FORCE"


@dataclass
class TeamMember:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    team_id: str = ""
    employee_id: str = ""
    role_in_team: str = "MEMBER"  # e.g., LEAD, MEMBER, ADVISOR
    allocation_percentage: float = 100.0
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    removed_at: datetime | None = None


@dataclass
class TeamHealth:
    team_id: str = ""
    utilization_rate: float = 0.0
    capability_coverage_pct: float = 100.0
    open_blockers_count: int = 0
    status: str = "HEALTHY"
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Team:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    code: str = ""
    purpose: str = ""
    team_type: TeamType = TeamType.TEMPORARY
    project_id: str | None = None
    department_ids: list[str] = field(default_factory=list)
    manager_id: str | None = None
    status: TeamStatus = TeamStatus.PROPOSED
    capabilities: list[str] = field(default_factory=list)
    creation_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    dissolved_at: datetime | None = None
    members: list[TeamMember] = field(default_factory=list)

    def activate(self) -> None:
        if self.status in (TeamStatus.DISSOLVING, TeamStatus.DISSOLVED):
            raise ValueError(f"Cannot activate team in status {self.status}")
        self.status = TeamStatus.ACTIVE

    def start_dissolving(self) -> None:
        self.status = TeamStatus.DISSOLVING

    def dissolve(self) -> None:
        self.status = TeamStatus.DISSOLVED
        self.dissolved_at = datetime.now(UTC)

    def add_member(self, employee_id: str, role_in_team: str = "MEMBER", allocation_percentage: float = 100.0) -> TeamMember:
        # Check if active member already exists
        for m in self.members:
            if m.employee_id == employee_id and m.removed_at is None:
                raise ValueError(f"Employee {employee_id} is already an active member of team {self.id}")
        member = TeamMember(
            team_id=self.id,
            employee_id=employee_id,
            role_in_team=role_in_team,
            allocation_percentage=allocation_percentage,
        )
        self.members.append(member)
        return member

    def remove_member(self, employee_id: str) -> None:
        for m in self.members:
            if m.employee_id == employee_id and m.removed_at is None:
                m.removed_at = datetime.now(UTC)
                return
        raise ValueError(f"Employee {employee_id} is not an active member of team {self.id}")
