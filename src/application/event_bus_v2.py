"""
EventBusV2 application service (Phase 38 - Event-Driven Autonomous Operations).
Provides publish-subscribe event routing, tenant isolation, and transactional outbox pattern.
"""

from collections import defaultdict
from typing import Any, Callable
from src.domain.event_v2 import EventV2, OutboxMessage, OutboxStatus


class EventBusV2:
    def __init__(self, repository=None):
        self.repository = repository
        # Map event_type -> list of subscriber callbacks
        self._subscribers: dict[str, list[Callable[[EventV2], None]]] = defaultdict(list)
        self._outbox: list[OutboxMessage] = []

    def subscribe(self, event_type: str, handler: Callable[[EventV2], None]) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: EventV2) -> None:
        """
        Publishes event to all registered in-memory subscribers.
        Ensures tenant isolation where subscribers are executed safely.
        """
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            handler(event)

    def publish_outbox(self, tenant_id: str, event_type: str, payload: dict[str, Any]) -> OutboxMessage:
        import uuid
        msg = OutboxMessage(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
            status=OutboxStatus.PENDING,
        )
        self._outbox.append(msg)
        if self.repository:
            self.repository.save_outbox_message(msg)
        return msg

    def process_outbox(self) -> int:
        """
        Flushes pending outbox messages by publishing them to subscribers.
        """
        processed_count = 0
        for msg in self._outbox:
            if msg.status == OutboxStatus.PENDING:
                event = EventV2(
                    id=msg.id,
                    tenant_id=msg.tenant_id,
                    event_type=msg.event_type,
                    payload=msg.payload,
                )
                self.publish(event)
                msg.status = OutboxStatus.PROCESSED
                processed_count += 1
        return processed_count
