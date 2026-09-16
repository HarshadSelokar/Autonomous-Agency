"""
Unit tests for MessageDeliveryService outbox delivery, status transitions, and retries.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.message_delivery_service import MessageDeliveryService
from src.domain.message import DeliveryState, Message, MessageType


@pytest.mark.asyncio
async def test_send_and_queue_message_success() -> None:
    msg_repo = MagicMock()
    outbox_repo = MagicMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    service = MessageDeliveryService(
        message_repository=msg_repo,
        outbox_repository=outbox_repo,
        event_dispatcher=event_dispatcher,
    )

    msg = Message(
        id="m100",
        conversation_id="c1",
        sender_employee_id="emp-1",
        message_type=MessageType.INFORMATION,
        content="System update",
    )
    msg_repo.save.side_effect = lambda m: m

    delivered = await service.send_and_queue_message(msg, recipients=["emp-2"])

    assert delivered.delivery_state == DeliveryState.DELIVERED
    outbox_repo.create_outbox_message.assert_called_once()
    assert event_dispatcher.publish.await_count == 2


@pytest.mark.asyncio
async def test_acknowledge_message_success() -> None:
    msg_repo = MagicMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    service = MessageDeliveryService(
        message_repository=msg_repo,
        event_dispatcher=event_dispatcher,
    )

    msg = Message(
        id="m100",
        conversation_id="c1",
        sender_employee_id="emp-1",
        message_type=MessageType.TASK_ASSIGNMENT,
        content="New task assigned",
    )
    msg_repo.get_by_id.return_value = msg
    msg_repo.save.side_effect = lambda m: m

    ack = await service.acknowledge_message("m100", participant_id="emp-2")

    assert ack.delivery_state == DeliveryState.ACKNOWLEDGED
    assert "emp-2" in ack.acknowledgements
    event_dispatcher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_outbox_queue_success() -> None:
    msg_repo = MagicMock()
    outbox_repo = MagicMock()

    item1 = MagicMock()
    item1.id = "out-1"
    item1.payload_json = '{"message_id": "m1"}'

    outbox_repo.get_pending_messages.return_value = [item1]

    service = MessageDeliveryService(
        message_repository=msg_repo,
        outbox_repository=outbox_repo,
    )

    count = await service.process_outbox_queue()

    assert count == 1
    outbox_repo.mark_processed.assert_called_once_with("out-1")
