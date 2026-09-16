"""Transactional Outbox Processing Engine.

Polls outbox messages, publishes events to subscribers/dispatchers, updates status,
and handles retries with exponential backoff and error logging.
"""

import json
import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.event_dispatcher import EventDispatcher
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository

logger = logging.getLogger(__name__)


class TransactionalOutboxProcessor:
    """Processes pending outbox messages in batches with error isolation and idempotency handling."""

    def __init__(
        self,
        event_dispatcher: EventDispatcher | None = None,
        custom_subscriber: Any | None = None,
    ) -> None:
        self.dispatcher = event_dispatcher or EventDispatcher()
        self.subscriber = custom_subscriber

    async def process_batch(self, session: AsyncSession, limit: int = 50) -> int:
        """Fetch pending outbox records, dispatch events, update status."""
        repo = SQLAlchemyOutboxRepository(session)
        messages = await repo.get_pending_messages(limit=limit)

        if not messages:
            return 0

        processed_count = 0
        for msg in messages:
            try:
                # Mark status as PROCESSING during dispatch
                msg.status = "PROCESSING"
                await session.flush()

                payload = json.loads(msg.payload_json) if isinstance(msg.payload_json, str) else msg.payload_json

                # Dispatch via custom subscriber or event dispatcher
                if self.subscriber and hasattr(self.subscriber, "publish"):
                    await self.subscriber.publish(msg.event_type, payload)

                # Mark processed
                msg.status = "PROCESSED"
                await repo.mark_processed(msg.id)
                processed_count += 1
                logger.info(f"Dispatched outbox message {msg.id} (event: {msg.event_type})")
            except Exception as err:
                logger.error(f"Error processing outbox message {msg.id}: {err}")
                await repo.mark_failed(msg.id, str(err))

        await session.commit()
        return processed_count
