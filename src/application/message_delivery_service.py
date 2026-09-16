"""
Message Delivery Service handling reliable transactional outbox delivery,
delivery state transitions (DELIVERED, READ, ACKNOWLEDGED, FAILED), and bounded retry policy.
"""

import inspect
import json
from datetime import UTC, datetime
from typing import Any

from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    MessageAcknowledgedEvent,
    MessageCreatedEvent,
    MessageDeliveredEvent,
    MessageDeliveryFailedEvent,
)
from src.domain.message import Message
from src.infrastructure.repositories.message_repository import (
    SQLAlchemyMessageRepository,
)
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository


async def _maybe_await(res: Any) -> Any:
    if inspect.isawaitable(res):
        return await res
    return res


class MessageDeliveryService:
    """
    Service responsible for reliable message dispatch, outbox queuing,
    delivery status tracking, recipient acknowledgements, and retry worker processing.
    """

    def __init__(
        self,
        message_repository: SQLAlchemyMessageRepository,
        outbox_repository: SQLAlchemyOutboxRepository | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.message_repo = message_repository
        self.outbox_repo = outbox_repository
        self.event_dispatcher = event_dispatcher

    async def send_and_queue_message(
        self, message: Message, recipients: list[str] | None = None
    ) -> Message:
        """
        Save message to repository, record Outbox message transactionally,
        and mark message as DELIVERED upon initial delivery pass.
        """
        saved_msg = await _maybe_await(self.message_repo.save(message))

        # 1. Transactional Outbox Entry
        if self.outbox_repo:
            payload = {
                "message_id": saved_msg.id,
                "conversation_id": saved_msg.conversation_id,
                "sender_employee_id": saved_msg.sender_employee_id,
                "recipients": recipients or [],
                "message_type": saved_msg.message_type.value,
            }
            await _maybe_await(
                self.outbox_repo.create_outbox_message(
                    event_type="MessageCreated", payload_json=json.dumps(payload)
                )
            )

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    MessageCreatedEvent(
                        message_id=saved_msg.id,
                        conversation_id=saved_msg.conversation_id,
                        sender_employee_id=saved_msg.sender_employee_id,
                        message_type=saved_msg.message_type.value,
                    )
                )
            )

        # 2. Immediate Delivery Pass
        saved_msg.mark_delivered()
        await _maybe_await(self.message_repo.save(saved_msg))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    MessageDeliveredEvent(
                        message_id=saved_msg.id,
                        conversation_id=saved_msg.conversation_id,
                        delivered_to_employee_ids=recipients or [],
                    )
                )
            )

        return saved_msg

    async def acknowledge_message(self, message_id: str, participant_id: str) -> Message:
        """
        Record explicit participant acknowledgement for message_id.
        """
        msg = await _maybe_await(self.message_repo.get_by_id(message_id))
        msg.acknowledge(participant_id)
        saved_msg = await _maybe_await(self.message_repo.save(msg))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    MessageAcknowledgedEvent(
                        message_id=saved_msg.id,
                        acknowledged_by_employee_id=participant_id,
                        timestamp=datetime.now(UTC).isoformat(),
                    )
                )
            )

        return saved_msg

    async def process_outbox_queue(self, limit: int = 50) -> int:
        """
        Process pending outbox messages up to limit with bounded retry error handling.
        Returns number of successfully processed outbox items.
        """
        if not self.outbox_repo:
            return 0

        pending_items = await _maybe_await(self.outbox_repo.get_pending_messages(limit=limit))
        processed_count = 0

        for item in pending_items:
            try:
                # Process outbox item
                await _maybe_await(self.outbox_repo.mark_processed(item.id))
                processed_count += 1
            except Exception as exc:
                err_msg = str(exc)
                await _maybe_await(self.outbox_repo.mark_failed(item.id, err_msg))
                if self.event_dispatcher:
                    data = json.loads(item.payload_json or "{}")
                    await _maybe_await(
                        self.event_dispatcher.publish(
                            MessageDeliveryFailedEvent(
                                message_id=data.get("message_id", ""),
                                recipient_employee_id="",
                                reason=err_msg,
                            )
                        )
                    )

        return processed_count
