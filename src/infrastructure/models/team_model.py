"""SQLAlchemy ORM Models for Teams and Team Members."""

import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.team import Team, TeamMember, TeamStatus, TeamType
from src.infrastructure.database import Base


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="")
    team_type: Mapped[str] = mapped_column(String(32), nullable=False, default="TEMPORARY")
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    department_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    manager_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    capabilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    creation_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    dissolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    members: Mapped[list["TeamMemberModel"]] = relationship(
        "TeamMemberModel", back_populates="team", cascade="all, delete-orphan", lazy="joined"
    )

    def to_domain(self) -> Team:
        depts = json.loads(self.department_ids_json) if self.department_ids_json else []
        caps = json.loads(self.capabilities_json) if self.capabilities_json else []
        domain_members = [m.to_domain() for m in self.members] if self.members else []
        return Team(
            id=self.id,
            name=self.name,
            code=self.code,
            purpose=self.purpose,
            team_type=TeamType(self.team_type),
            project_id=self.project_id,
            department_ids=depts,
            manager_id=self.manager_id,
            status=TeamStatus(self.status),
            capabilities=caps,
            creation_reason=self.creation_reason,
            created_at=self.created_at,
            dissolved_at=self.dissolved_at,
            members=domain_members,
        )

    @classmethod
    def from_domain(cls, entity: Team) -> "TeamModel":
        depts_json = json.dumps(entity.department_ids)
        caps_json = json.dumps(entity.capabilities)
        team_model = cls(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            purpose=entity.purpose,
            team_type=entity.team_type.value if hasattr(entity.team_type, "value") else str(entity.team_type),
            project_id=entity.project_id,
            department_ids_json=depts_json,
            manager_id=entity.manager_id,
            status=entity.status.value if hasattr(entity.status, "value") else str(entity.status),
            capabilities_json=caps_json,
            creation_reason=entity.creation_reason,
            created_at=entity.created_at,
            dissolved_at=entity.dissolved_at,
        )
        if entity.members:
            team_model.members = [TeamMemberModel.from_domain(m) for m in entity.members]
        return team_model


class TeamMemberModel(Base):
    __tablename__ = "team_members"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(64), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role_in_team: Mapped[str] = mapped_column(String(64), nullable=False, default="MEMBER")
    allocation_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped[TeamModel] = relationship("TeamModel", back_populates="members")

    def to_domain(self) -> TeamMember:
        return TeamMember(
            id=self.id,
            team_id=self.team_id,
            employee_id=self.employee_id,
            role_in_team=self.role_in_team,
            allocation_percentage=self.allocation_percentage,
            assigned_at=self.assigned_at,
            removed_at=self.removed_at,
        )

    @classmethod
    def from_domain(cls, entity: TeamMember) -> "TeamMemberModel":
        return cls(
            id=entity.id,
            team_id=entity.team_id,
            employee_id=entity.employee_id,
            role_in_team=entity.role_in_team,
            allocation_percentage=entity.allocation_percentage,
            assigned_at=entity.assigned_at,
            removed_at=entity.removed_at,
        )
