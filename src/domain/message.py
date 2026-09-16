"""
Message domain entity, MessageType enum, MessageReference, and DeliveryState enum.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import DomainError


class MessageError(DomainError):
    """Raised when an invalid message operation or transition occurs."""

    pass


class MessageType(str, Enum):
    INFORMATION = "INFORMATION"
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    STATUS_UPDATE = "STATUS_UPDATE"
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    TASK_RESULT = "TASK_RESULT"
    BLOCKER = "BLOCKER"
    ESCALATION = "ESCALATION"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    APPROVAL_RESPONSE = "APPROVAL_RESPONSE"
    DECISION = "DECISION"
    NOTIFICATION = "NOTIFICATION"


class DeliveryState(str, Enum):
    CREATED = "CREATED"
    DELIVERED = "DELIVERED"
    READ = "READ"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"


class MessageReference:
    """
    Domain entity linking a Message to an organizational entity (Task, Objective, Plan, Decision, Artifact).
    """

    def __init__(
        self,
        reference_type: str,
        reference_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not reference_type or not reference_type.strip():
            raise MessageError("Reference type cannot be empty.")
        if not reference_id or not reference_id.strip():
            raise MessageError("Reference ID cannot be empty.")
        self.reference_type = reference_type.strip().lower()
        self.reference_id = reference_id.strip()
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageReference":
        return cls(
            reference_type=data["reference_type"],
            reference_id=data["reference_id"],
            metadata=data.get("metadata", {}),
        )


class Message:
    """
    First-class Message domain entity representing an auditable organizational message.
    Preserves strict separation of identities: EMPLOYEE ≠ AGENT ≠ LLM.
    """

    def __init__(
        self,
        id: str | None = None,
        conversation_id: str = "",
        sender_employee_id: str = "",
        sender_agent_id: str | None = None,
        sender_run_id: str | None = None,
        message_type: MessageType | str = MessageType.INFORMATION,
        subject: str = "",
        content: str = "",
        priority: str = "medium",
        references: list[MessageReference] | None = None,
        reply_to_message_id: str | None = None,
        correlation_id: str | None = None,
        delivery_state: DeliveryState | str = DeliveryState.CREATED,
        acknowledgements: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        if not sender_employee_id or not sender_employee_id.strip():
            raise MessageError("Sender employee ID cannot be empty.")
        if not content and not subject:
            raise MessageError("Message must contain a subject or content.")

        self.id = id or f"msg-{uuid.uuid4().hex[:8]}"
        self.conversation_id = conversation_id
        self.sender_employee_id = sender_employee_id.strip()
        self.sender_agent_id = sender_agent_id
        self.sender_run_id = sender_run_id
        self.message_type = (
            MessageType(message_type) if isinstance(message_type, str) else message_type
        )
        self.subject = subject
        self.content = content
        self.priority = priority.lower()
        self.references = references or []
        self.reply_to_message_id = reply_to_message_id
        self.correlation_id = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        self.delivery_state = (
            DeliveryState(delivery_state) if isinstance(delivery_state, str) else delivery_state
        )
        self.acknowledgements = acknowledgements or {}
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)

    def add_reference(self, reference: MessageReference) -> None:
        if not any(
            r.reference_type == reference.reference_type
            and r.reference_id == reference.reference_id
            for r in self.references
        ):
            self.references.append(reference)
            self.updated_at = datetime.now(UTC)

    def mark_delivered(self) -> None:
        if self.delivery_state == DeliveryState.CREATED:
            self.delivery_state = DeliveryState.DELIVERED
            self.updated_at = datetime.now(UTC)

    def mark_read(self) -> None:
        if self.delivery_state in {DeliveryState.CREATED, DeliveryState.DELIVERED}:
            self.delivery_state = DeliveryState.READ
            self.updated_at = datetime.now(UTC)

    def acknowledge(self, participant_id: str) -> None:
        if not participant_id or not participant_id.strip():
            raise MessageError("Participant ID for acknowledgement cannot be empty.")
        self.acknowledgements[participant_id.strip()] = datetime.now(UTC).isoformat()
        self.delivery_state = DeliveryState.ACKNOWLEDGED
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_employee_id": self.sender_employee_id,
            "sender_agent_id": self.sender_agent_id,
            "sender_run_id": self.sender_run_id,
            "message_type": self.message_type.value,
            "subject": self.subject,
            "content": self.content,
            "priority": self.priority,
            "references": [r.to_dict() for r in self.references],
            "reply_to_message_id": self.reply_to_message_id,
            "correlation_id": self.correlation_id,
            "delivery_state": self.delivery_state.value,
            "acknowledgements": self.acknowledgements,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
