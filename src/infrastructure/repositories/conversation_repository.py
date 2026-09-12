"""
SQLAlchemy Repository implementation for Conversation domain entity.
"""

import inspect
from typing import Any, Sequence

from sqlalchemy import select

from src.domain.conversation import Conversation, ConversationType
from src.domain.exceptions import DomainError
from src.infrastructure.models.conversation_model import (
    ConversationModel,
    conversation_domain_to_model,
    conversation_model_to_domain,
)


class ConversationNotFoundError(DomainError):
    def __init__(self, conversation_id: str) -> None:
        super().__init__(f"Conversation with ID '{conversation_id}' was not found.")
        self.conversation_id = conversation_id


class SQLAlchemyConversationRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def _get(self, entity_id: str) -> ConversationModel | None:
        res = self.session.get(ConversationModel, entity_id)
        if inspect.isawaitable(res):
            return await res
        return res

    async def _scalars_all(self, stmt: Any) -> Sequence[ConversationModel]:
        res = self.session.scalars(stmt)
        if inspect.isawaitable(res):
            res = await res
        all_res = res.all()
        if inspect.isawaitable(all_res):
            all_res = await all_res
        return all_res

    async def save(self, conversation: Conversation) -> Conversation:
        model = await self._get(conversation.id)
        if model is None:
            model = conversation_domain_to_model(conversation)
            self.session.add(model)
        else:
            updated_model = conversation_domain_to_model(conversation)
            model.title = updated_model.title
            model.conversation_type = updated_model.conversation_type
            model.created_by_employee_id = updated_model.created_by_employee_id
            model.participants_json = updated_model.participants_json
            model.related_objective_id = updated_model.related_objective_id
            model.related_plan_id = updated_model.related_plan_id
            model.related_task_id = updated_model.related_task_id
            model.related_project_id = updated_model.related_project_id
            model.status = updated_model.status
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at

        flush_res = self.session.flush()
        if inspect.isawaitable(flush_res):
            await flush_res
        return conversation_model_to_domain(model)

    async def get_by_id(self, conversation_id: str) -> Conversation:
        model = await self._get(conversation_id)
        if model is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation_model_to_domain(model)

    async def get_by_task_id(self, task_id: str) -> list[Conversation]:
        stmt = select(ConversationModel).where(ConversationModel.related_task_id == task_id)
        models = await self._scalars_all(stmt)
        return [conversation_model_to_domain(m) for m in models]

    async def get_by_type(self, conversation_type: ConversationType) -> list[Conversation]:
        stmt = select(ConversationModel).where(
            ConversationModel.conversation_type == conversation_type.value
        )
        models = await self._scalars_all(stmt)
        return [conversation_model_to_domain(m) for m in models]

    async def get_all(self) -> list[Conversation]:
        stmt = select(ConversationModel)
        models = await self._scalars_all(stmt)
        return [conversation_model_to_domain(m) for m in models]

    async def delete(self, conversation_id: str) -> None:
        model = await self._get(conversation_id)
        if model is not None:
            delete_res = self.session.delete(model)
            if inspect.isawaitable(delete_res):
                await delete_res
            flush_res = self.session.flush()
            if inspect.isawaitable(flush_res):
                await flush_res
