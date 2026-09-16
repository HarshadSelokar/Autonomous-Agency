"""
Unit tests for MeetingContextBuilder and MeetingTranscript.
"""

import pytest

from src.application.meeting_context_builder import MeetingAccessDeniedError, MeetingContextBuilder
from src.domain.conversation import Conversation
from src.domain.meeting import Meeting, MeetingPurpose, ParticipantRole
from src.domain.message import Message, MessageType
from src.domain.transcript import MeetingTranscript
from tests.unit.test_meeting_scheduling import MemoryMeetingRepository


class MemoryConversationRepository:
    def __init__(self) -> None:
        self.conversations: dict[str, Conversation] = {}

    async def get_by_id(self, conv_id: str) -> Conversation | None:
        return self.conversations.get(conv_id)


class MemoryMessageRepository:
    def __init__(self) -> None:
        self.messages: dict[str, list[Message]] = {}

    async def list_by_conversation_id(self, conv_id: str, limit: int = 50) -> list[Message]:
        return self.messages.get(conv_id, [])[:limit]


def test_meeting_transcript_entry() -> None:
    transcript = MeetingTranscript(meeting_id="m-1")
    e1 = transcript.add_entry(speaker_employee_id="emp-1", content="Proposal for API Gateway")
    assert len(transcript.entries) == 1
    assert e1.speaker_employee_id == "emp-1"
    assert e1.content == "Proposal for API Gateway"


@pytest.mark.asyncio
async def test_meeting_context_builder_authorized() -> None:
    meeting_repo = MemoryMeetingRepository()
    msg_repo = MemoryMessageRepository()

    meeting = Meeting(
        id="m-context-1",
        title="Gateway Design Sync",
        purpose=MeetingPurpose.REVIEW,
        organizer_employee_id="emp-mgr",
        conversation_id="conv-1",
    )
    meeting.add_participant("emp-dev", role=ParticipantRole.REQUIRED)
    meeting.add_agenda_item(item_id="ag-1", title="API Gateway Benchmarks")
    await meeting_repo.save(meeting)

    msg_repo.messages["conv-1"] = [
        Message(
            id="msg-1",
            conversation_id="conv-1",
            sender_employee_id="emp-dev",
            message_type=MessageType.INFORMATION,
            content="Kong vs Envoy comparison complete.",
        )
    ]

    builder = MeetingContextBuilder(meeting_repo=meeting_repo, message_repo=msg_repo)

    # Authorized participant context build
    context = await builder.build_context("m-context-1", requesting_employee_id="emp-dev")
    assert context["meeting_id"] == "m-context-1"
    assert "Gateway Design Sync" in context["framed_prompt_context"]
    assert "Kong vs Envoy" in context["framed_prompt_context"]
    assert "=== BEGIN UNTRUSTED MEETING CONTEXT" in context["framed_prompt_context"]


@pytest.mark.asyncio
async def test_meeting_context_builder_unauthorized_denied() -> None:
    meeting_repo = MemoryMeetingRepository()
    meeting = Meeting(
        id="m-context-2",
        title="Executive Strategy Sync",
        purpose=MeetingPurpose.DECISION,
        organizer_employee_id="emp-ceo",
    )
    await meeting_repo.save(meeting)

    builder = MeetingContextBuilder(meeting_repo=meeting_repo)

    # Unauthorized employee access fails
    with pytest.raises(MeetingAccessDeniedError, match="is not authorized to access context"):
        await builder.build_context("m-context-2", requesting_employee_id="emp-unauthorized")
