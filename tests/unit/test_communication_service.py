"""
Unit tests for CommunicationService high-level orchestration, blockers, and escalations.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.communication_service import CommunicationService
from src.domain.conversation import Conversation, ConversationType
from src.domain.message import Message, MessageType


@pytest.mark.asyncio
async def test_create_conversation_success() -> None:
    conv_repo = MagicMock()
    msg_repo = MagicMock()
    router = MagicMock()
    delivery_service = MagicMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    conv_repo.save.side_effect = lambda c: c

    service = CommunicationService(
        conversation_repository=conv_repo,
        message_repository=msg_repo,
        message_router=router,
        message_delivery_service=delivery_service,
        event_dispatcher=event_dispatcher,
    )

    conv = await service.create_conversation(
        title="Sprint Sync",
        conversation_type=ConversationType.TEAM,
        created_by_employee_id="emp-1",
        participant_employee_ids=["emp-2", "emp-3"],
    )

    assert conv.title == "Sprint Sync"
    assert len(conv.participants) == 3
    event_dispatcher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_report_blocker_creates_task_conversation() -> None:
    conv_repo = MagicMock()
    msg_repo = MagicMock()
    router = MagicMock()
    delivery_service = MagicMock()

    conv_repo.get_by_task_id.return_value = []
    conv_repo.save.side_effect = lambda c: c

    sent_msg = Message(
        id="m-blocker",
        conversation_id="c-task",
        sender_employee_id="emp-dev",
        message_type=MessageType.BLOCKER,
        content="Missing API keys",
    )
    router.route_and_validate.side_effect = (
        lambda message, conversation, authenticated_caller_id=None: message
    )
    delivery_service.send_and_queue_message = AsyncMock(return_value=sent_msg)

    service = CommunicationService(
        conversation_repository=conv_repo,
        message_repository=msg_repo,
        message_router=router,
        message_delivery_service=delivery_service,
    )

    msg = await service.report_blocker(
        sender_employee_id="emp-dev",
        task_id="task-99",
        blocker_description="Missing API keys",
        manager_employee_id="emp-mgr",
    )

    assert msg.message_type == MessageType.BLOCKER
    assert msg.id == "m-blocker"
    delivery_service.send_and_queue_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_escalate_blocker_success() -> None:
    conv_repo = MagicMock()
    msg_repo = MagicMock()
    router = MagicMock()
    delivery_service = MagicMock()

    orig_msg = Message(
        id="m-orig",
        conversation_id="c-orig",
        sender_employee_id="emp-dev",
        message_type=MessageType.BLOCKER,
        content="Original blocker",
    )
    conv = Conversation(id="c-orig", created_by_employee_id="emp-dev")

    msg_repo.get_by_id.return_value = orig_msg
    conv_repo.get_by_id.return_value = conv
    conv_repo.save.side_effect = lambda c: c

    escalated_msg = Message(
        id="m-esc",
        conversation_id="c-orig",
        sender_employee_id="emp-mgr",
        message_type=MessageType.ESCALATION,
        content="Escalating blocker",
    )
    router.route_and_validate.side_effect = (
        lambda message, conversation, authenticated_caller_id=None: message
    )
    delivery_service.send_and_queue_message = AsyncMock(return_value=escalated_msg)

    service = CommunicationService(
        conversation_repository=conv_repo,
        message_repository=msg_repo,
        message_router=router,
        message_delivery_service=delivery_service,
    )

    result = await service.escalate_blocker(
        sender_manager_id="emp-mgr",
        task_id="task-99",
        original_blocker_message_id="m-orig",
        higher_manager_id="emp-director",
        escalation_reason="Manager cannot resolve credentials issue",
    )

    assert result.message_type == MessageType.ESCALATION
    assert conv.has_participant("emp-director")
