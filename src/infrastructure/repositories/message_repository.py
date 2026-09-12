"""
SQLAlchemy Repository implementation for Message domain entity.
"""

import inspect
from typing import Any, Sequence

from sqlalchemy import select

from src.domain.exceptions import DomainError
from src.domain.message import DeliveryState, Message, MessageType
from src.infrastructure.models.message_model import (
    MessageModel,
    message_domain_to_model,
    message_model_to_domain,
)


class MessageNotFoundError(DomainError):
    def __init__(self, message_id: str) -> None:
        super().__init__(f"Message with ID '{message_id}' was not found.")
        self.message_id = message_id


class SQLAlchemyMessageRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def _get(self, entity_id: str) -> MessageModel | None:
        res = self.session.get(MessageModel, entity_id)
        if inspect.isawaitable(res):
            return await res
        return res

    async def _scalars_all(self, stmt: Any) -> Sequence[MessageModel]:
        res = self.session.scalars(stmt)
        if inspect.isawaitable(res):
            res = await res
        all_res = res.all()
        if inspect.isawaitable(all_res):
            all_res = await all_res
        return all_res

    async def save(self, message: Message) -> Message:
        model = await self._get(message.id)
        if model is None:
            model = message_domain_to_model(message)
            self.session.add(model)
        else:
            updated_model = message_domain_to_model(message)
            model.conversation_id = updated_model.conversation_id
            model.sender_employee_id = updated_model.sender_employee_id
            model.sender_agent_id = updated_model.sender_agent_id
            model.sender_run_id = updated_model.sender_run_id
            model.message_type = updated_model.message_type
            model.subject = updated_model.subject
            model.content = updated_model.content
            model.priority = updated_model.priority
            model.references_json = updated_model.references_json
            model.reply_to_message_id = updated_model.reply_to_message_id
            model.correlation_id = updated_model.correlation_id
            model.delivery_state = updated_model.delivery_state
            model.acknowledgements_json = updated_model.acknowledgements_json
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at

        flush_res = self.session.flush()
        if inspect.isawaitable(flush_res):
            await flush_res
        return message_model_to_domain(model)

    async def get_by_id(self, message_id: str) -> Message:
        model = await self._get(message_id)
        if model is None:
            raise MessageNotFoundError(message_id)
        return message_model_to_domain(model)

    async def get_by_conversation_id(self, conversation_id: str) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc(), MessageModel.id.asc())
        )
        models = await self._scalars_all(stmt)
        return [message_model_to_domain(m) for m in models]

    async def get_by_sender_employee_id(self, employee_id: str) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.sender_employee_id == employee_id)
            .order_by(MessageModel.created_at.desc())
        )
        models = await self._scalars_all(stmt)
        return [message_model_to_domain(m) for m in models]

    async def get_by_type(self, message_type: MessageType) -> list[Message]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.message_type == message_type.value)
            .order_by(MessageModel.created_at.desc())
        )
        models = await self._scalars_all(stmt)
        return [message_model_to_domain(m) for m in models]

    async def get_by_delivery_state(self, delivery_state: DeliveryState) -> list[Message]:
        stmt = select(MessageModel).where(MessageModel.delivery_state == delivery_state.value)
        models = await self._scalars_all(stmt)
        return [message_model_to_domain(m) for m in models]

    async def get_all(self) -> list[Message]:
        stmt = select(MessageModel).order_by(MessageModel.created_at.asc())
        models = await self._scalars_all(stmt)
        return [message_model_to_domain(m) for m in models]

    async def delete(self, message_id: str) -> None:
        model = await self._get(message_id)
        if model is not None:
            delete_res = self.session.delete(model)
            if inspect.isawaitable(delete_res):
                await delete_res
            flush_res = self.session.flush()
            if inspect.isawaitable(flush_res):
                await flush_res
