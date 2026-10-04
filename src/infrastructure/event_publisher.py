"""
Outbox event publishers.

The worker drains the transactional outbox and hands each message to a publisher.
RedisEventPublisher fans events out over Redis pub/sub so every API process can relay
them (for example to Pixel Office WebSocket clients).
"""

import json
import logging
from typing import Any

from src.infrastructure.redis_client import redis_manager

logger = logging.getLogger(__name__)

EVENTS_CHANNEL = "agency.events"


class RedisEventPublisher:
    def __init__(self, client: Any | None = None, channel: str = EVENTS_CHANNEL) -> None:
        self._client = client
        self.channel = channel

    async def publish(self, event_type: str, payload: Any) -> None:
        client = self._client or redis_manager.get_client()
        message = json.dumps({"event_type": event_type, "payload": payload}, default=str)
        # Raises when Redis is unreachable, which leaves the outbox message for retry
        await client.publish(self.channel, message)


class LoggingEventPublisher:
    """Fallback when Redis is not available: events are logged, not dropped silently."""

    async def publish(self, event_type: str, payload: Any) -> None:
        logger.info("Outbox event %s: %s", event_type, json.dumps(payload, default=str)[:500])
