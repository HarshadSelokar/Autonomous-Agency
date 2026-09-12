"""
Unit tests for Message domain entity, MessageType, DeliveryState, and MessageReference.
"""

import pytest

from src.domain.message import (
    DeliveryState,
    Message,
    MessageError,
    MessageReference,
    MessageType,
)


def test_message_reference_creation() -> None:
    ref = MessageReference(reference_type="task", reference_id="task-100")
    assert ref.reference_type == "task"
    assert ref.reference_id == "task-100"

    data = ref.to_dict()
    reconstructed = MessageReference.from_dict(data)
    assert reconstructed.reference_type == "task"
    assert reconstructed.reference_id == "task-100"


def test_message_creation_validation() -> None:
    with pytest.raises(MessageError, match="Sender employee ID cannot be empty"):
        Message(sender_employee_id="", content="Hello")

    with pytest.raises(MessageError, match="Message must contain a subject or content"):
        Message(sender_employee_id="emp-1", content="", subject="")


def test_message_lifecycle_states() -> None:
    msg = Message(
        conversation_id="conv-1",
        sender_employee_id="emp-1",
        sender_agent_id="agent-1",
        sender_run_id="run-1",
        message_type=MessageType.BLOCKER,
        subject="Database down",
        content="Unable to connect to Postgres DB",
    )

    assert msg.delivery_state == DeliveryState.CREATED
    assert msg.sender_employee_id == "emp-1"
    assert msg.sender_agent_id == "agent-1"
    assert msg.message_type == MessageType.BLOCKER

    msg.mark_delivered()
    assert msg.delivery_state == DeliveryState.DELIVERED

    msg.mark_read()
    assert msg.delivery_state == DeliveryState.READ

    msg.acknowledge("mgr-1")
    assert msg.delivery_state == DeliveryState.ACKNOWLEDGED
    assert "mgr-1" in msg.acknowledgements


def test_message_references() -> None:
    msg = Message(
        conversation_id="conv-1",
        sender_employee_id="emp-1",
        content="Task update for T100",
    )

    ref = MessageReference(reference_type="task", reference_id="T100")
    msg.add_reference(ref)
    assert len(msg.references) == 1

    # Duplicate reference ignored
    msg.add_reference(ref)
    assert len(msg.references) == 1
