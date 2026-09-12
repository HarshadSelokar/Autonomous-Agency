"""
High-level Communication Application Service orchestrating conversations,
messages, task-linked blockers, manager escalations, and threaded replies.
"""

import inspect
from typing import Any

from src.application.event_dispatcher import EventDispatcher
from src.application.message_delivery_service import MessageDeliveryService
from src.application.message_router import MessageRouter
from src.domain.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationType,
)
from src.domain.events import ConversationCreatedEvent
from src.domain.exceptions import DomainError
from src.domain.message import Message, MessageReference, MessageType
from src.infrastructure.repositories.conversation_repository import (
    SQLAlchemyConversationRepository,
)
from src.infrastructure.repositories.message_repository import (
    SQLAlchemyMessageRepository,
)


class CommunicationServiceError(DomainError):
    """Raised when communication service operations fail."""

    pass


async def _maybe_await(res: Any) -> Any:
    if inspect.isawaitable(res):
        return await res
    return res


class CommunicationService:
    """
    Core Company OS Communication Service managing organizational collaboration.
    Ensures message routing, delivery tracking, task-linked blocker reporting,
    and escalation protocols while preserving Task Engine authority.
    """

    def __init__(
        self,
        conversation_repository: SQLAlchemyConversationRepository,
        message_repository: SQLAlchemyMessageRepository,
        message_router: MessageRouter,
        message_delivery_service: MessageDeliveryService,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.conversation_repo = conversation_repository
        self.message_repo = message_repository
        self.router = message_router
        self.delivery_service = message_delivery_service
        self.event_dispatcher = event_dispatcher

    async def create_conversation(
        self,
        title: str,
        conversation_type: ConversationType | str = ConversationType.DIRECT,
        created_by_employee_id: str = "",
        participant_employee_ids: list[str] | None = None,
        related_objective_id: str | None = None,
        related_plan_id: str | None = None,
        related_task_id: str | None = None,
        related_project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """Create and persist a new Conversation entity with explicit participants."""
        conv = Conversation(
            title=title,
            conversation_type=conversation_type,
            created_by_employee_id=created_by_employee_id,
            related_objective_id=related_objective_id,
            related_plan_id=related_plan_id,
            related_task_id=related_task_id,
            related_project_id=related_project_id,
            metadata=metadata or {},
        )

        for p_id in participant_employee_ids or []:
            conv.add_participant(ConversationParticipant(participant_id=p_id))

        saved_conv = await _maybe_await(self.conversation_repo.save(conv))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    ConversationCreatedEvent(
                        conversation_id=saved_conv.id,
                        conversation_type=saved_conv.conversation_type.value,
                        created_by_employee_id=saved_conv.created_by_employee_id,
                    )
                )
            )

        return saved_conv

    async def send_message(
        self,
        sender_employee_id: str,
        conversation_id: str,
        message_type: MessageType | str,
        content: str,
        subject: str = "",
        priority: str = "medium",
        references: list[MessageReference] | None = None,
        reply_to_message_id: str | None = None,
        sender_agent_id: str | None = None,
        sender_run_id: str | None = None,
        authenticated_caller_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """
        Validate sender authority, route message, queue transactional outbox, and trigger delivery.
        """
        conv = await _maybe_await(self.conversation_repo.get_by_id(conversation_id))

        msg = Message(
            conversation_id=conversation_id,
            sender_employee_id=sender_employee_id,
            sender_agent_id=sender_agent_id,
            sender_run_id=sender_run_id,
            message_type=message_type,
            subject=subject,
            content=content,
            priority=priority,
            references=references or [],
            reply_to_message_id=reply_to_message_id,
            metadata=metadata or {},
        )

        # 1. Deterministic Validation & Routing Pass
        validated_msg = await _maybe_await(
            self.router.route_and_validate(
                message=msg,
                conversation=conv,
                authenticated_caller_id=authenticated_caller_id,
            )
        )

        # 2. Extract recipient employee IDs from conversation
        recipients = [
            p.participant_id for p in conv.participants if p.participant_id != sender_employee_id
        ]

        # 3. Delivery & Outbox Processing
        delivered_msg = await self.delivery_service.send_and_queue_message(
            message=validated_msg, recipients=recipients
        )

        return delivered_msg

    async def report_blocker(
        self,
        sender_employee_id: str,
        task_id: str,
        blocker_description: str,
        manager_employee_id: str,
        sender_agent_id: str | None = None,
        sender_run_id: str | None = None,
    ) -> Message:
        """
        Report a task execution blocker to manager.
        Creates a task-linked conversation if none exists, sends BLOCKER message.
        Does NOT alter Task Engine state directly.
        """
        convs = await _maybe_await(self.conversation_repo.get_by_task_id(task_id))
        if convs:
            conv = convs[0]
        else:
            conv = await self.create_conversation(
                title=f"Task {task_id} Discussion",
                conversation_type=ConversationType.TASK,
                created_by_employee_id=sender_employee_id,
                participant_employee_ids=[sender_employee_id, manager_employee_id],
                related_task_id=task_id,
            )

        if not conv.has_participant(manager_employee_id):
            conv.add_participant(ConversationParticipant(participant_id=manager_employee_id))
            await _maybe_await(self.conversation_repo.save(conv))

        ref = MessageReference(reference_type="task", reference_id=task_id)
        msg = await self.send_message(
            sender_employee_id=sender_employee_id,
            conversation_id=conv.id,
            message_type=MessageType.BLOCKER,
            subject=f"BLOCKER reported on Task '{task_id}'",
            content=blocker_description,
            priority="high",
            references=[ref],
            sender_agent_id=sender_agent_id,
            sender_run_id=sender_run_id,
        )
        return msg

    async def escalate_blocker(
        self,
        sender_manager_id: str,
        task_id: str,
        original_blocker_message_id: str,
        higher_manager_id: str,
        escalation_reason: str,
    ) -> Message:
        """
        Escalate an unresolved blocker up the manager hierarchy.
        """
        orig_msg = await _maybe_await(self.message_repo.get_by_id(original_blocker_message_id))
        conv = await _maybe_await(self.conversation_repo.get_by_id(orig_msg.conversation_id))

        if not conv.has_participant(higher_manager_id):
            conv.add_participant(ConversationParticipant(participant_id=higher_manager_id))
            await _maybe_await(self.conversation_repo.save(conv))

        ref_task = MessageReference(reference_type="task", reference_id=task_id)
        ref_msg = MessageReference(
            reference_type="message", reference_id=original_blocker_message_id
        )

        msg = await self.send_message(
            sender_employee_id=sender_manager_id,
            conversation_id=conv.id,
            message_type=MessageType.ESCALATION,
            subject=f"ESCALATION: Task '{task_id}' Blocker",
            content=escalation_reason,
            priority="critical",
            references=[ref_task, ref_msg],
            reply_to_message_id=original_blocker_message_id,
        )
        return msg

    async def reply_to_message(
        self,
        original_message_id: str,
        sender_employee_id: str,
        content: str,
        message_type: MessageType | str = MessageType.RESPONSE,
        sender_agent_id: str | None = None,
        sender_run_id: str | None = None,
    ) -> Message:
        """
        Send a threaded reply referencing an existing message.
        """
        orig_msg = await _maybe_await(self.message_repo.get_by_id(original_message_id))
        reply = await self.send_message(
            sender_employee_id=sender_employee_id,
            conversation_id=orig_msg.conversation_id,
            message_type=message_type,
            content=content,
            reply_to_message_id=original_message_id,
            sender_agent_id=sender_agent_id,
            sender_run_id=sender_run_id,
        )
        return reply
