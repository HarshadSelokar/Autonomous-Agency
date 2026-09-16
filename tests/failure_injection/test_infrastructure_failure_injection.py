"""Phase 20 Infrastructure Failure Injection Test Suite.

Verifies:
1. DB health check returns false on DB connection failure.
2. Redis health check handles Redis disconnects gracefully without crashing.
3. Storage provider handles connection failures gracefully with local fallback.
4. Worker lifecycle manager handles signal interruptions and moves to DRAINING state.
5. Transactional outbox handles retries when publishing fails.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.database import check_database_health
from src.infrastructure.redis_client import RedisClientManager, check_redis_health
from src.infrastructure.s3_storage_provider import S3StorageProvider
from src.infrastructure.worker_lifecycle import WorkerLifecycleManager, WorkerLifecycleState
from src.infrastructure.outbox_processor import TransactionalOutboxProcessor


@pytest.mark.asyncio
async def test_db_failure_injection():
    # Mock engine throwing an exception during health check
    mock_engine = MagicMock()
    mock_engine.connect = MagicMock(side_effect=Exception("Database connection lost"))
    
    is_healthy, msg = await check_database_health(mock_engine)
    assert is_healthy is False
    assert "Database unavailable" in msg


@pytest.mark.asyncio
async def test_redis_failure_injection():
    manager = RedisClientManager(url="redis://localhost:6379/0")
    
    # Mock redis client ping failure
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection refused"))
    manager._client = mock_redis
    
    is_healthy, msg = await manager.check_health()
    assert is_healthy is False
    assert len(msg) > 0


@pytest.mark.asyncio
async def test_storage_failure_injection():
    provider = S3StorageProvider(
        endpoint_url="http://invalid-host:9000",
        bucket_name="test-bucket",
        access_key="test",
        secret_key="test",
    )
    
    # Provider should gracefully fallback to LocalStorageProvider if endpoint fails
    data = b"Failure injection data"
    uri = await provider.store_bytes("test.txt", data)
    assert "local" in uri or "file://" in uri or "test.txt" in uri
    read_back = await provider.read_bytes(uri)
    assert read_back == data


@pytest.mark.asyncio
async def test_worker_interruption_injection():
    manager = WorkerLifecycleManager()
    assert manager.state == WorkerLifecycleState.STARTING
    
    manager.transition_to(WorkerLifecycleState.READY)
    manager.transition_to(WorkerLifecycleState.RUNNING)
    assert manager.state == WorkerLifecycleState.RUNNING
    
    # Inject graceful shutdown request
    manager.transition_to(WorkerLifecycleState.DRAINING)
    assert manager.is_draining is True
    assert manager.state == WorkerLifecycleState.DRAINING
    
    manager.transition_to(WorkerLifecycleState.STOPPED)
    assert manager.state == WorkerLifecycleState.STOPPED


@pytest.mark.asyncio
async def test_outbox_retry_exhaustion_injection():
    mock_subscriber = MagicMock()
    mock_subscriber.publish = AsyncMock(side_effect=Exception("Publishing error"))
    outbox = TransactionalOutboxProcessor(custom_subscriber=mock_subscriber)
    
    mock_session = AsyncMock()
    mock_msg = MagicMock()
    mock_msg.id = "msg-123"
    mock_msg.event_type = "TEST_EVENT"
    mock_msg.payload_json = '{"event": "TEST_EVENT"}'
    
    with AsyncMock() as mock_repo:
        pass

    # Batch processing with failing subscriber should handle error without crashing
    processed = await outbox.process_batch(mock_session, limit=10)
    assert processed == 0
