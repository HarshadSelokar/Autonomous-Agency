"""
Unit tests for MessageRouter sender authority and routing validation.
"""

from unittest.mock import MagicMock
import pytest

from src.application.message_router import (
    CommunicationAuthorizationError,
    CommunicationValidationError,
    MessageRouter,
)
from src.domain.conversation import Conversation, ConversationParticipant, ConversationType
from src.domain.employee import Employee, EmployeeStatus
from src.domain.message import Message, MessageType


@pytest.mark.asyncio
async def test_validate_sender_authority_success() -> None:
    emp_repo = MagicMock()
    emp_repo.get_by_id.return_value = Employee(
        id="emp-1",
        employee_code="E001",
        name="Alice",
        title="Engineer",
        role="IC",
        agent_id="agent-1",
        status=EmployeeStatus.ACTIVE,
    )

    router = MessageRouter(employee_repository=emp_repo)
    await router.validate_sender_authority(
        sender_employee_id="emp-1", authenticated_caller_id="emp-1"
    )


@pytest.mark.asyncio
async def test_sender_spoofing_rejected() -> None:
    emp_repo = MagicMock()
    router = MessageRouter(employee_repository=emp_repo)

    with pytest.raises(CommunicationAuthorizationError, match="Sender spoofing rejected"):
        await router.validate_sender_authority(
            sender_employee_id="emp-ceo", authenticated_caller_id="emp-hacker"
        )


@pytest.mark.asyncio
async def test_terminated_employee_sender_rejected() -> None:
    emp_repo = MagicMock()
    emp_repo.get_by_id.return_value = Employee(
        id="emp-1",
        employee_code="E001",
        name="Bob",
        title="Engineer",
        role="IC",
        agent_id="agent-1",
        status=EmployeeStatus.TERMINATED,
    )

    router = MessageRouter(employee_repository=emp_repo)
    with pytest.raises(CommunicationAuthorizationError, match="Terminated employee"):
        await router.validate_sender_authority(sender_employee_id="emp-1")


@pytest.mark.asyncio
async def test_route_and_validate_non_member_rejected() -> None:
    emp_repo = MagicMock()
    emp_repo.get_by_id.return_value = Employee(
        id="emp-1",
        employee_code="E001",
        name="Alice",
        title="Engineer",
        role="IC",
        agent_id="agent-1",
        status=EmployeeStatus.ACTIVE,
    )

    router = MessageRouter(employee_repository=emp_repo)

    conv = Conversation(
        id="c1",
        title="Private Team Chat",
        conversation_type=ConversationType.TEAM,
        created_by_employee_id="emp-other",
    )
    # emp-1 is not in participants

    msg = Message(
        conversation_id="c1",
        sender_employee_id="emp-1",
        content="Hello secret team",
    )

    with pytest.raises(CommunicationAuthorizationError, match="not a participant"):
        await router.route_and_validate(message=msg, conversation=conv)
