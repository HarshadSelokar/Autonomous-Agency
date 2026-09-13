"""
MeetingContextBuilder Application Layer for Phase 6.
Builds relevance-controlled, authorization-validated context packages with prompt security framing.
"""

from typing import Any

from src.domain.exceptions import ObjectiveValidationError
from src.domain.repository import (
    MeetingRepositoryInterface,
    ObjectiveRepositoryInterface,
)


class MeetingAccessDeniedError(ObjectiveValidationError):
    """Raised when an unauthorized actor attempts to access meeting context."""

    pass


class MeetingContextBuilder:
    def __init__(
        self,
        meeting_repo: MeetingRepositoryInterface,
        conversation_repo: Any = None,
        message_repo: Any = None,
        objective_repo: ObjectiveRepositoryInterface | None = None,
        task_repo: Any = None,
    ) -> None:
        self.meeting_repo = meeting_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.objective_repo = objective_repo
        self.task_repo = task_repo

    async def build_context(
        self,
        meeting_id: str,
        requesting_employee_id: str,
        max_messages: int = 20,
    ) -> dict[str, Any]:
        """Build structured, authorization-checked meeting context."""
        meeting = await self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise ObjectiveValidationError(f"Meeting {meeting_id} not found.")

        # Authorization check: requester must be a participant or organizer
        if requesting_employee_id not in meeting.participants and requesting_employee_id != meeting.organizer_employee_id:
            raise MeetingAccessDeniedError(
                f"Employee {requesting_employee_id} is not authorized to access context for meeting {meeting_id}."
            )

        # Related entities
        objective_title = None
        if meeting.objective_id and self.objective_repo:
            obj = await self.objective_repo.get_by_id(meeting.objective_id)
            if obj:
                objective_title = obj.title

        task_title = None
        if meeting.task_id and self.task_repo:
            tsk = await self.task_repo.get_by_id(meeting.task_id)
            if tsk:
                task_title = tsk.title

        # Phase 5 Messages
        recent_messages: list[dict[str, Any]] = []
        if meeting.conversation_id and self.message_repo:
            msgs = await self.message_repo.list_by_conversation_id(
                meeting.conversation_id, limit=max_messages
            )
            for m in msgs:
                m_type = getattr(m, "message_type", getattr(m, "payload_type", "INFORMATION"))
                type_str = m_type.value if hasattr(m_type, "value") else str(m_type)
                recent_messages.append(
                    {
                        "sender_employee_id": m.sender_employee_id,
                        "sender_agent_id": getattr(m, "sender_agent_id", None),
                        "payload_type": type_str,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
                    }
                )

        # Prompt Security Framing
        agenda_summary = [
            f"{item.order}. [{item.status.value}] {item.title}" + (f": {item.description}" if item.description else "")
            for item in meeting.agenda_items
        ]

        framed_prompt_context = (
            f"=== BEGIN UNTRUSTED MEETING CONTEXT (ID: {meeting.id}) ===\n"
            f"Title: {meeting.title}\n"
            f"Purpose: {meeting.purpose.value}\n"
            f"Status: {meeting.status.value}\n"
            f"Organizer: {meeting.organizer_employee_id}\n"
            f"Objective: {objective_title or meeting.objective_id or 'None'}\n"
            f"Task: {task_title or meeting.task_id or 'None'}\n"
            f"Agenda:\n" + ("\n".join(f" - {a}" for a in agenda_summary) if agenda_summary else " - None") + "\n"
            f"Recent Discussion Messages ({len(recent_messages)}):\n"
        )
        for msg in recent_messages:
            sender = msg["sender_agent_id"] or msg["sender_employee_id"]
            framed_prompt_context += f" - [{msg['created_at']}] {sender}: {msg['content']}\n"
        framed_prompt_context += "=== END UNTRUSTED MEETING CONTEXT ==="

        return {
            "meeting_id": meeting.id,
            "title": meeting.title,
            "purpose": meeting.purpose.value,
            "status": meeting.status.value,
            "organizer_employee_id": meeting.organizer_employee_id,
            "participants": [
                {"employee_id": p.employee_id, "role": p.role.value, "agent_id": p.agent_id}
                for p in meeting.participants.values()
            ],
            "agenda_items": [
                {"order": item.order, "title": item.title, "status": item.status.value}
                for item in meeting.agenda_items
            ],
            "recent_messages": recent_messages,
            "framed_prompt_context": framed_prompt_context,
        }
