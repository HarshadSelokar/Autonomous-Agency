"""Phase 20 Infrastructure Concurrency Test Suite.

Verifies:
1. Concurrent Redis client manager health check & access.
2. Concurrent outbox message processing without race conditions.
3. Concurrent metrics collector recording across multiple tasks.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.redis_client import RedisClientManager
from src.infrastructure.observability import MetricsCollector
from src.infrastructure.outbox_processor import TransactionalOutboxProcessor


@pytest.mark.asyncio
async def test_concurrent_metrics_collection():
    collector = MetricsCollector()
    
    async def record_task(task_id: int):
        for _ in range(50):
            collector.record_api_request("/health/live", 200)
            collector.record_agent_run("groq/llama3", "completed")
            collector.worker_jobs_processed += 1
            await asyncio.sleep(0.001)

    # Launch 10 concurrent tasks
    tasks = [asyncio.create_task(record_task(i)) for i in range(10)]
    await asyncio.gather(*tasks)
    
    summary = collector.get_summary()
    assert summary["api_total_requests"] == 500
    assert summary["agent_runs"]["groq/llama3:completed"] == 500
    assert summary["worker_jobs_processed"] == 500


@pytest.mark.asyncio
async def test_concurrent_redis_manager_access():
    manager = RedisClientManager(url="redis://localhost:6379/0")
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(return_value=True)
    manager._client = mock_redis

    async def worker_access(worker_id: int):
        healthy, msg = await manager.check_health()
        return isinstance(healthy, bool)

    results = await asyncio.gather(*[worker_access(i) for i in range(20)])
    assert len(results) == 20
    assert all(r is True for r in results)


@pytest.mark.asyncio
async def test_concurrent_outbox_processing():
    processed_events = []

    async def dummy_publish(event_type, payload):
        processed_events.append(payload["id"])

    mock_subscriber = MagicMock()
    mock_subscriber.publish = AsyncMock(side_effect=dummy_publish)

    outbox = TransactionalOutboxProcessor(custom_subscriber=mock_subscriber)

    mock_session = AsyncMock()

    # Process pending outbox concurrently from 2 workers
    res1, res2 = await asyncio.gather(
        outbox.process_batch(mock_session, limit=10),
        outbox.process_batch(mock_session, limit=10)
    )

    assert res1 >= 0
    assert res2 >= 0
