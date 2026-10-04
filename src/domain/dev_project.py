"""
Software Studio domain: a dev project worked on by a small team of agents.

DevProject -> DevTicket (the board) -> ActivityEvent (the live feed).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ProjectStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"  # finished, but some tickets are blocked
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"  # the process running it stopped; can be restarted
    WAITING_FOR_QUOTA = "WAITING_FOR_QUOTA"  # every model is out of quota; resumes by itself


ACTIVE_PROJECT_STATUSES = {ProjectStatus.PLANNING, ProjectStatus.RUNNING}


class TicketStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    IN_REVIEW = "IN_REVIEW"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"  # reviewer approved; a human must sign off
    DONE = "DONE"
    BLOCKED = "BLOCKED"


IN_FLIGHT_TICKET_STATUSES = {
    TicketStatus.IN_PROGRESS,
    TicketStatus.TESTING,
    TicketStatus.IN_REVIEW,
    TicketStatus.AWAITING_APPROVAL,
}


class TeamRole(str, Enum):
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"
    QA = "QA"
    REVIEWER = "REVIEWER"


class TeamValidationError(ValueError):
    """Raised when a team does not have the roles a project needs."""


@dataclass
class TeamMember:
    id: str
    name: str
    role: TeamRole

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name, "role": self.role.value}


DEVELOPER_NAMES = ["Srujan", "Aditya Y", "Abhyudaya", "Arya", "Manthan", "Om"]


def default_team(project_id: str, developers: int = 1) -> list[TeamMember]:
    developers = max(1, min(developers, len(DEVELOPER_NAMES)))
    team = [TeamMember(id=f"{project_id}-manager", name="Aruhi", role=TeamRole.MANAGER)]
    for index in range(developers):
        suffix = "developer" if index == 0 else f"developer-{index + 1}"
        team.append(
            TeamMember(id=f"{project_id}-{suffix}", name=DEVELOPER_NAMES[index], role=TeamRole.DEVELOPER)
        )
    team.append(TeamMember(id=f"{project_id}-qa", name="Indrayani", role=TeamRole.QA))
    team.append(TeamMember(id=f"{project_id}-reviewer", name="Tanu", role=TeamRole.REVIEWER))
    return team


def validate_team(members: list[TeamMember]) -> None:
    """A team needs exactly one manager, QA and reviewer, and at least one developer."""
    counts = {role: sum(1 for m in members if m.role == role) for role in TeamRole}
    for role in (TeamRole.MANAGER, TeamRole.QA, TeamRole.REVIEWER):
        if counts[role] != 1:
            raise TeamValidationError(f"A team needs exactly one {role.value}, found {counts[role]}.")
    if not 1 <= counts[TeamRole.DEVELOPER] <= 6:
        raise TeamValidationError("A team needs between 1 and 6 developers.")
    if len({m.id for m in members}) != len(members):
        raise TeamValidationError("Team member ids must be unique.")
    if any(not m.name.strip() for m in members):
        raise TeamValidationError("Every team member needs a name.")


@dataclass
class DevProject:
    id: str
    name: str
    goal: str
    tenant_id: str | None = None
    status: ProjectStatus = ProjectStatus.CREATED
    repo_url: str | None = None
    local_path: str | None = None
    workspace_path: str = ""
    branch: str = ""
    base_commit: str = ""
    test_command: str | None = None
    engine: str = ""  # "loop" or "agy"; empty uses STUDIO_ENGINE
    provider: str = ""
    model: str = ""
    # Custom team as [{"id", "name", "role"}]; empty means the default team
    members: list[dict[str, str]] = field(default_factory=list)
    # A human must approve each ticket after the reviewer does, before it is merged
    require_approval: bool = False
    summary: str = ""
    failure_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def team(self) -> list[TeamMember]:
        if self.members:
            return [TeamMember(id=m["id"], name=m["name"], role=TeamRole(m["role"])) for m in self.members]
        return default_team(self.id)

    def set_team(self, members: list[TeamMember]) -> None:
        validate_team(members)
        self.members = [m.to_dict() for m in members]
        self.updated_at = datetime.now(UTC)

    def member(self, role: TeamRole) -> TeamMember:
        return next(m for m in self.team() if m.role == role)

    def developers(self) -> list[TeamMember]:
        return [m for m in self.team() if m.role == TeamRole.DEVELOPER]

    def set_status(self, status: ProjectStatus, failure_reason: str | None = None) -> None:
        self.status = status
        self.failure_reason = failure_reason
        self.updated_at = datetime.now(UTC)

    def add_usage(self, usage: dict[str, int]) -> None:
        for key, value in usage.items():
            self.usage[key] = self.usage.get(key, 0) + value


@dataclass
class DevTicket:
    id: str
    project_id: str
    sequence: int
    title: str
    description: str = ""
    acceptance_criteria: str = ""
    status: TicketStatus = TicketStatus.TODO
    depends_on: list[str] = field(default_factory=list)
    assignee_id: str | None = None
    attempts: int = 0
    feedback: str = ""
    commit_sha: str | None = None
    result_summary: str = ""
    # Human decision while AWAITING_APPROVAL: "", "APPROVED" or "REJECTED"
    approval: str = ""
    approval_feedback: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def move_to(self, status: TicketStatus, assignee_id: str | None = None) -> None:
        self.status = status
        self.assignee_id = assignee_id
        self.updated_at = datetime.now(UTC)


@dataclass
class ActivityEvent:
    project_id: str
    actor_id: str
    actor_name: str
    actor_role: str
    # status | tool_call | tool_result | message | ticket | project | human_message | violation
    kind: str
    summary: str
    ticket_id: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)
    sequence: int = 0  # assigned by the store, monotonically increasing per project
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
