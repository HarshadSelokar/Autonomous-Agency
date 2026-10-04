"""Unit tests: the worker publishes outbox events and failed publishes are retried."""

import json
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.infrastructure.database import Base
from src.infrastructure.event_publisher import EVENTS_CHANNEL, RedisEventPublisher
from src.infrastructure.models.outbox_model import OutboxMessageModel
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.worker import ProductionWorker


class FakeRedis:
    def __init__(self, fail_times: int = 0) -> None:
        self.published: list[tuple[str, str]] = []
        self.fail_times = fail_times

    async def publish(self, channel: str, message: str) -> None:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionError("redis down")
        self.published.append((channel, message))


async def make_factory() -> tuple[Any, async_sessionmaker]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def enqueue(factory: async_sessionmaker, event_type: str, payload: dict[str, Any]) -> str:
    async with factory() as db:
        message = await SQLAlchemyOutboxRepository(db).create_outbox_message(event_type, json.dumps(payload))
        await db.commit()
        return message.id


async def status_of(factory: async_sessionmaker, message_id: str) -> tuple[str, int]:
    async with factory() as db:
        model = await db.get(OutboxMessageModel, message_id)
        return model.status, model.retry_count


async def test_worker_publishes_outbox_events_to_redis():
    engine, factory = await make_factory()
    redis = FakeRedis()
    worker = ProductionWorker(session_factory=factory, event_publisher=RedisEventPublisher(client=redis))
    message_id = await enqueue(factory, "TaskCreatedEvent", {"task_id": "t-100"})

    assert await worker.run_once() == 1

    [(channel, raw)] = redis.published
    assert channel == EVENTS_CHANNEL
    assert json.loads(raw) == {"event_type": "TaskCreatedEvent", "payload": {"task_id": "t-100"}}
    assert await status_of(factory, message_id) == ("PROCESSED", 0)
    assert await worker.run_once() == 0  # not delivered twice
    await engine.dispose()


async def test_failed_publish_is_retried_not_lost():
    engine, factory = await make_factory()
    redis = FakeRedis(fail_times=1)
    worker = ProductionWorker(session_factory=factory, event_publisher=RedisEventPublisher(client=redis))
    message_id = await enqueue(factory, "TaskCreatedEvent", {"task_id": "t-1"})

    assert await worker.run_once() == 0
    assert await status_of(factory, message_id) == ("PENDING", 1)
    assert redis.published == []

    assert await worker.run_once() == 1
    assert await status_of(factory, message_id) == ("PROCESSED", 1)
    assert len(redis.published) == 1
    await engine.dispose()


async def test_message_fails_permanently_after_max_retries():
    engine, factory = await make_factory()
    worker = ProductionWorker(
        session_factory=factory, event_publisher=RedisEventPublisher(client=FakeRedis(fail_times=99))
    )
    message_id = await enqueue(factory, "TaskCreatedEvent", {})
    async with factory() as db:
        max_retries = (await db.get(OutboxMessageModel, message_id)).max_retries

    for _ in range(max_retries + 2):
        await worker.run_once()

    assert await status_of(factory, message_id) == ("FAILED", max_retries)
    await engine.dispose()
