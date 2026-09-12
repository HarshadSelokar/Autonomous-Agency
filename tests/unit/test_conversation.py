"""
Unit tests for Conversation domain entity, ConversationType enum, and ConversationParticipant.
"""

import pytest

from src.domain.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationType,
    ConversationTypeError,
)


def test_conversation_participant_creation() -> None:
    p = ConversationParticipant(
        participant_id="emp-101", participant_type="employee", role="member"
    )
    assert p.participant_id == "emp-101"
    assert p.participant_type == "employee"
    assert p.role == "member"

    data = p.to_dict()
    reconstructed = ConversationParticipant.from_dict(data)
    assert reconstructed.participant_id == "emp-101"


def test_conversation_participant_empty_id_raises() -> None:
    with pytest.raises(ConversationTypeError, match="Participant ID cannot be empty"):
        ConversationParticipant(participant_id="")


def test_conversation_creation_auto_adds_owner() -> None:
    conv = Conversation(
        title="Project Planning",
        conversation_type=ConversationType.TEAM,
        created_by_employee_id="emp-mgr",
        related_task_id="task-123",
    )

    assert conv.title == "Project Planning"
    assert conv.conversation_type == ConversationType.TEAM
    assert conv.has_participant("emp-mgr")
    assert conv.related_task_id == "task-123"


def test_conversation_add_and_remove_participant() -> None:
    conv = Conversation(
        title="Direct Chat",
        conversation_type=ConversationType.DIRECT,
        created_by_employee_id="emp-1",
    )

    p2 = ConversationParticipant(participant_id="emp-2")
    conv.add_participant(p2)
    assert conv.has_participant("emp-2")

    # Duplicate add ignored
    conv.add_participant(p2)
    assert len(conv.participants) == 2

    # Remove participant
    conv.remove_participant("emp-2")
    assert not conv.has_participant("emp-2")
    assert len(conv.participants) == 1
