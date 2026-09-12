"""
SQLAlchemy Repository implementation for Transactional Outbox.
"""

import inspect
from typing import Any, Sequence
import uuid

from sqlalchemy import select

from src.infrastructure.models.outbox_model import OutboxMessageModel


class SQLAlchemyOutboxRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def _get(self, entity_id: str) -> OutboxMessageModel | None:
        res = self.session.get(OutboxMessageModel, entity_id)
        if inspect.isawaitable(res):
            return await res
        return res

    async def _scalars_all(self, stmt: Any) -> Sequence[OutboxMessageModel]:
        res = self.session.scalars(stmt)
        if inspect.isawaitable(res):
            res = await res
        all_res = res.all()
        if inspect.isawaitable(all_res):
            all_res = await all_res
        return all_res

    async def create_outbox_message(
        self, event_type: str, payload_json: str, outbox_id: str | None = None
    ) -> OutboxMessageModel:
        model = OutboxMessageModel(
            id=outbox_id or f"out-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            payload_json=payload_json,
            status="PENDING",
        )
        self.session.add(model)
        flush_res = self.session.flush()
        if inspect.isawaitable(flush_res):
            await flush_res
        return model

    async def get_pending_messages(self, limit: int = 50) -> list[OutboxMessageModel]:
        stmt = (
            select(OutboxMessageModel)
            .where(OutboxMessageModel.status == "PENDING")
            .order_by(OutboxMessageModel.created_at.asc())
            .limit(limit)
        )
        models = await self._scalars_all(stmt)
        return list(models)

    async def mark_processed(self, outbox_id: str) -> None:
        model = await self._get(outbox_id)
        if model:
            model.status = "PROCESSED"
            flush_res = self.session.flush()
            if inspect.isawaitable(flush_res):
                await flush_res

    async def mark_failed(self, outbox_id: str, error_msg: str) -> None:
        model = await self._get(outbox_id)
        if model:
            model.retry_count += 1
            model.last_error = error_msg
            if model.retry_count >= model.max_retries:
                model.status = "FAILED"
            flush_res = self.session.flush()
            if inspect.isawaitable(flush_res):
                await flush_res
