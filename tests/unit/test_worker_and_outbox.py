"""Unit tests for Worker Lifecycle & Transactional Outbox Processing."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.infrastructure.database import Base
from src.infrastructure.outbox_processor import TransactionalOutboxProcessor
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.worker import ProductionWorker
from src.infrastructure.worker_lifecycle import WorkerLifecycleManager, WorkerLifecycleState


@pytest.mark.asyncio
async def test_worker_lifecycle_state_transitions():
    mgr = WorkerLifecycleManager()
    assert mgr.state == WorkerLifecycleState.STARTING
    assert mgr.is_running is False

    mgr.transition_to(WorkerLifecycleState.READY)
    assert mgr.is_running is True

    mgr.transition_to(WorkerLifecycleState.RUNNING)
    assert mgr.is_running is True

    mgr.transition_to(WorkerLifecycleState.DRAINING)
    assert mgr.is_draining is True
    assert mgr.is_running is False

    mgr.transition_to(WorkerLifecycleState.STOPPED)
    assert mgr.is_stopped is True


@pytest.mark.asyncio
async def test_outbox_processor_batch():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Insert test outbox message
    async with session_factory() as db:
        repo = SQLAlchemyOutboxRepository(db)
        await repo.create_outbox_message("TaskCreatedEvent", '{"task_id": "t-100"}')
        await db.commit()

    # Process outbox via TransactionalOutboxProcessor
    processor = TransactionalOutboxProcessor()
    async with session_factory() as db:
        count = await processor.process_batch(db, limit=10)
        assert count == 1

    # Verify message status updated to PROCESSED
    async with session_factory() as db:
        repo = SQLAlchemyOutboxRepository(db)
        pending = await repo.get_pending_messages()
        assert len(pending) == 0

    await engine.dispose()


@pytest.mark.asyncio
async def test_production_worker_run_once():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    worker = ProductionWorker(session_factory=session_factory)
    processed = await worker.run_once()
    assert processed == 0
    assert worker.jobs_processed_count == 0

    await engine.dispose()
