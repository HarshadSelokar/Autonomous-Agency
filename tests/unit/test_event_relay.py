"""Unit tests: events the worker publishes to Redis reach WebSocket clients."""

import asyncio
import json
from typing import Any
from uuid import UUID

from src.application.office_realtime_service import OfficeRealtimeBroadcaster, PixelOfficeConnection
from src.infrastructure.event_publisher import EVENTS_CHANNEL, RedisEventPublisher
from src.infrastructure.event_relay import RedisEventRelay


class FakePubSub:
    def __init__(self, redis: "FakeRedis") -> None:
        self.redis = redis
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def subscribe(self, channel: str) -> None:
        if self.redis.fail_subscribes > 0:
            self.redis.fail_subscribes -= 1
            raise ConnectionError("redis down")
        self.redis.subscribers.setdefault(channel, []).append(self)
        await self.queue.put({"type": "subscribe", "data": 1})

    async def unsubscribe(self, channel: str) -> None:
        if self in self.redis.subscribers.get(channel, []):
            self.redis.subscribers[channel].remove(self)

    async def listen(self):
        while True:
            yield await self.queue.get()


class FakeRedis:
    def __init__(self, fail_subscribes: int = 0) -> None:
        self.subscribers: dict[str, list[FakePubSub]] = {}
        self.fail_subscribes = fail_subscribes

    def pubsub(self) -> FakePubSub:
        return FakePubSub(self)

    async def publish(self, channel: str, message: Any) -> None:
        for subscriber in self.subscribers.get(channel, []):
            await subscriber.queue.put({"type": "message", "data": message})


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.sent.append(payload)


async def until(condition, timeout: float = 5.0) -> None:
    for _ in range(int(timeout / 0.01)):
        if condition():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition was not met in time")


async def test_published_event_reaches_connected_websocket_clients():
    redis = FakeRedis()
    broadcaster = OfficeRealtimeBroadcaster()
    socket = FakeWebSocket()
    broadcaster.register_connection(
        PixelOfficeConnection("c1", UUID("00000000-0000-0000-0000-000000000001"), websocket=socket)
    )
    relay = RedisEventRelay(broadcaster.broadcast_payload, client=redis)
    relay.start()
    await until(lambda: redis.subscribers.get(EVENTS_CHANNEL))

    await RedisEventPublisher(client=redis).publish("TaskCreatedEvent", {"task_id": "t-1"})
    await until(lambda: socket.sent)

    assert socket.sent == [{"event_type": "TaskCreatedEvent", "payload": {"task_id": "t-1"}}]
    await relay.stop()
    assert redis.subscribers[EVENTS_CHANNEL] == []  # unsubscribed on shutdown


async def test_relay_survives_bad_messages_and_failing_handlers():
    redis = FakeRedis()
    received: list[dict[str, Any]] = []

    async def handler(event: dict[str, Any]) -> None:
        if event.get("event_type") == "boom":
            raise RuntimeError("client exploded")
        received.append(event)

    relay = RedisEventRelay(handler, client=redis)
    relay.start()
    await until(lambda: redis.subscribers.get(EVENTS_CHANNEL))

    await redis.publish(EVENTS_CHANNEL, "{not json")
    await redis.publish(EVENTS_CHANNEL, json.dumps([1, 2]))
    await redis.publish(EVENTS_CHANNEL, json.dumps({"event_type": "boom"}))
    await redis.publish(EVENTS_CHANNEL, json.dumps({"event_type": "ok"}))
    await until(lambda: received)

    assert received == [{"event_type": "ok"}]
    await relay.stop()


async def test_relay_reconnects_after_redis_was_down():
    redis = FakeRedis(fail_subscribes=2)
    received: list[dict[str, Any]] = []

    async def handler(event: dict[str, Any]) -> None:
        received.append(event)

    relay = RedisEventRelay(handler, client=redis, retry_seconds=0.01)
    relay.start()
    await until(lambda: redis.subscribers.get(EVENTS_CHANNEL))

    await redis.publish(EVENTS_CHANNEL, json.dumps({"event_type": "after-recovery"}))
    await until(lambda: received)
    assert redis.fail_subscribes == 0
    await relay.stop()
