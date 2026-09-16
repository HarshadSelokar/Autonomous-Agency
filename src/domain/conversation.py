"""
Conversation domain entity, ConversationType enum, and ConversationParticipant domain model.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import DomainError


class ConversationTypeError(DomainError):
    """Raised when an invalid conversation operation or transition occurs."""

    pass


class ConversationType(str, Enum):
    DIRECT = "DIRECT"
    TEAM = "TEAM"
    TASK = "TASK"
    OBJECTIVE = "OBJECTIVE"
    MANAGER = "MANAGER"
    ESCALATION = "ESCALATION"


class ConversationParticipant:
    """
    Domain model representing an explicit participant in a Conversation.
    Participant may be an Employee, a Human user, or an Organizational Role.
    """

    def __init__(
        self,
        participant_id: str,
        participant_type: str = "employee",
        role: str = "member",
        joined_at: datetime | None = None,
    ) -> None:
        if not participant_id or not participant_id.strip():
            raise ConversationTypeError("Participant ID cannot be empty.")
        self.participant_id = participant_id.strip()
        self.participant_type = participant_type.strip()
        self.role = role.strip()
        self.joined_at = joined_at or datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "participant_type": self.participant_type,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationParticipant":
        joined_at = (
            datetime.fromisoformat(data["joined_at"])
            if isinstance(data.get("joined_at"), str)
            else data.get("joined_at")
        )
        return cls(
            participant_id=data["participant_id"],
            participant_type=data.get("participant_type", "employee"),
            role=data.get("role", "member"),
            joined_at=joined_at,
        )


class Conversation:
    """
    First-class Conversation domain entity representing a structured communication context.
    """

    def __init__(
        self,
        id: str | None = None,
        title: str = "",
        conversation_type: ConversationType | str = ConversationType.DIRECT,
        created_by_employee_id: str = "",
        participants: list[ConversationParticipant] | None = None,
        related_objective_id: str | None = None,
        related_plan_id: str | None = None,
        related_task_id: str | None = None,
        related_project_id: str | None = None,
        status: str = "active",
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.id = id or f"conv-{uuid.uuid4().hex[:8]}"
        self.title = title or f"Conversation {self.id}"
        self.conversation_type = (
            ConversationType(conversation_type)
            if isinstance(conversation_type, str)
            else conversation_type
        )
        self.created_by_employee_id = created_by_employee_id
        self.participants = participants or []
        self.related_objective_id = related_objective_id
        self.related_plan_id = related_plan_id
        self.related_task_id = related_task_id
        self.related_project_id = related_project_id
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

        # Auto-add creator as participant if provided and not already included
        if self.created_by_employee_id and not self.has_participant(self.created_by_employee_id):
            self.add_participant(
                ConversationParticipant(participant_id=self.created_by_employee_id, role="owner")
            )

    def has_participant(self, participant_id: str) -> bool:
        return any(p.participant_id == participant_id for p in self.participants)

    def add_participant(self, participant: ConversationParticipant) -> None:
        if self.has_participant(participant.participant_id):
            return
        self.participants.append(participant)
        self.updated_at = datetime.now(UTC)

    def remove_participant(self, participant_id: str) -> None:
        initial_len = len(self.participants)
        self.participants = [p for p in self.participants if p.participant_id != participant_id]
        if len(self.participants) < initial_len:
            self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "conversation_type": self.conversation_type.value,
            "created_by_employee_id": self.created_by_employee_id,
            "participants": [p.to_dict() for p in self.participants],
            "related_objective_id": self.related_objective_id,
            "related_plan_id": self.related_plan_id,
            "related_task_id": self.related_task_id,
            "related_project_id": self.related_project_id,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
