"""Production Background Worker Entry Point & Daemon Runner."""

import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.config import settings
from src.infrastructure.database import engine
from src.infrastructure.event_publisher import LoggingEventPublisher, RedisEventPublisher
from src.infrastructure.outbox_processor import TransactionalOutboxProcessor
from src.infrastructure.redis_client import HAS_REDIS
from src.infrastructure.worker_lifecycle import WorkerLifecycleManager, WorkerLifecycleState

logger = logging.getLogger(__name__)


class ProductionWorker:
    """Production async background worker daemon for outbox dispatching and task execution."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        event_publisher: Any | None = None,
    ) -> None:
        self.session_factory = session_factory or async_sessionmaker(engine, expire_on_commit=False)
        self.lifecycle = WorkerLifecycleManager(drain_timeout_seconds=settings.WORKER_DRAIN_TIMEOUT)
        if event_publisher is None:
            event_publisher = RedisEventPublisher() if HAS_REDIS else LoggingEventPublisher()
        self.outbox_processor = TransactionalOutboxProcessor(custom_subscriber=event_publisher)
        self.jobs_processed_count: int = 0

    async def run_once(self) -> int:
        """Execute a single processing iteration over pending outbox/task workloads."""
        processed = 0
        async with self.session_factory() as session:
            try:
                processed += await self.outbox_processor.process_batch(session, limit=25)
            except Exception as err:
                logger.error(f"Worker processing error: {err}")
        self.jobs_processed_count += processed
        return processed

    async def start(self) -> None:
        """Start daemon worker loop with graceful drain handling."""
        self.lifecycle.register_signal_handlers()
        self.lifecycle.transition_to(WorkerLifecycleState.READY)
        self.lifecycle.transition_to(WorkerLifecycleState.RUNNING)

        logger.info("Production background worker started and polling...")

        while self.lifecycle.is_running:
            try:
                processed = await self.run_once()
                if processed == 0:
                    await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                logger.info("Worker loop cancelled.")
                break
            except Exception as err:
                logger.error(f"Unexpected worker loop exception: {err}")
                await asyncio.sleep(1.0)

        # Handle DRAINING state
        if self.lifecycle.is_draining:
            logger.info("Worker is draining remaining in-flight tasks...")
            await self.run_once()
            self.lifecycle.transition_to(WorkerLifecycleState.STOPPED)

        logger.info(f"Worker stopped cleanly. Total jobs processed: {self.jobs_processed_count}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker = ProductionWorker()
    asyncio.run(worker.start())
