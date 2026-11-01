"""
Relays events published by the worker (Redis pub/sub) into this API process, so they can be
pushed to connected WebSocket clients. Keeps retrying while Redis is unreachable.
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from src.infrastructure.event_publisher import EVENTS_CHANNEL
from src.infrastructure.redis_client import redis_manager

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[Any]]


class RedisEventRelay:
    def __init__(
        self,
        handler: EventHandler,
        client: Any | None = None,
        channel: str = EVENTS_CHANNEL,
        retry_seconds: float = 5.0,
    ) -> None:
        self.handler = handler
        self._client = client
        self.channel = channel
        self.retry_seconds = retry_seconds
        self._task: asyncio.Task[None] | None = None
        self.delivered = 0

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="redis-event-relay")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def _run(self) -> None:
        warned = False
        while True:
            try:
                await self._listen()
                warned = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if not warned:  # one line while Redis is down, not one every few seconds
                    logger.warning("Event relay cannot reach Redis (%s); retrying.", exc)
                    warned = True
            await asyncio.sleep(self.retry_seconds)

    async def _listen(self) -> None:
        client = self._client or redis_manager.get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(self.channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                await self._deliver(message.get("data"))
        finally:
            await pubsub.unsubscribe(self.channel)

    async def _deliver(self, raw: Any) -> None:
        try:
            event = json.loads(raw)
        except (TypeError, ValueError):
            logger.warning("Dropped a malformed event from Redis.")
            return
        if not isinstance(event, dict):
            return
        try:
            await self.handler(event)
            self.delivered += 1
        except Exception:  # one bad client or event must not stop the relay
            logger.exception("Event relay handler failed for %s", event.get("event_type"))
