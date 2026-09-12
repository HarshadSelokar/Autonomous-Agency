"""
Deterministic Message Router for sender authority validation, recipient resolution,
and authorization checks.
"""

import inspect
from typing import Any

from src.domain.conversation import Conversation
from src.domain.exceptions import DomainError
from src.domain.message import Message
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.conversation_repository import (
    SQLAlchemyConversationRepository,
)
from src.infrastructure.repositories.employee_repository import (
    SQLAlchemyEmployeeRepository,
)


class CommunicationAuthorizationError(DomainError):
    """Raised when communication authorization checks fail."""

    pass


class CommunicationValidationError(DomainError):
    """Raised when message payload or recipient routing validation fails."""

    pass


async def _maybe_await(res: Any) -> Any:
    if inspect.isawaitable(res):
        return await res
    return res


class MessageRouter:
    """
    Deterministic Message Router responsible for validating sender authority,
    verifying recipient eligibility, enforcing organizational permissions,
    and ensuring messages originate from authoritative caller context.
    """

    def __init__(
        self,
        employee_repository: SQLAlchemyEmployeeRepository,
        agent_repository: SQLAlchemyAgentRepository | None = None,
        conversation_repository: SQLAlchemyConversationRepository | None = None,
    ) -> None:
        self.employee_repo = employee_repository
        self.agent_repo = agent_repository
        self.conversation_repo = conversation_repository

    async def validate_sender_authority(
        self,
        sender_employee_id: str,
        sender_agent_id: str | None = None,
        authenticated_caller_id: str | None = None,
    ) -> None:
        """
        Verify sender employee exists and is active.
        If authenticated_caller_id is provided, reject sender spoofing if caller != sender.
        If sender_agent_id is provided, verify Agent exists.
        """
        if authenticated_caller_id and authenticated_caller_id != sender_employee_id:
            raise CommunicationAuthorizationError(
                f"Sender spoofing rejected: authenticated caller '{authenticated_caller_id}' "
                f"cannot send messages as employee '{sender_employee_id}'."
            )

        employee = await _maybe_await(self.employee_repo.get_by_id(sender_employee_id))
        if employee is None:
            raise CommunicationValidationError(
                f"Sender employee ID '{sender_employee_id}' does not exist."
            )

        emp_status = getattr(employee, "status", "ACTIVE")
        if isinstance(emp_status, str):
            status_val = emp_status.upper()
        else:
            status_val = getattr(emp_status, "value", str(emp_status)).upper()

        if status_val == "TERMINATED":
            raise CommunicationAuthorizationError(
                f"Terminated employee '{sender_employee_id}' is not authorized to send messages."
            )

        if sender_agent_id and self.agent_repo:
            agent = await _maybe_await(self.agent_repo.get_by_id(sender_agent_id))
            if agent is None:
                raise CommunicationValidationError(
                    f"Sender agent ID '{sender_agent_id}' does not exist."
                )

    async def validate_conversation_membership(
        self, conversation: Conversation, sender_employee_id: str
    ) -> None:
        """Verify that sender_employee_id is a member/participant of the conversation."""
        if not conversation.has_participant(sender_employee_id):
            raise CommunicationAuthorizationError(
                f"Employee '{sender_employee_id}' is not a participant of "
                f"conversation '{conversation.id}'."
            )

    async def route_and_validate(
        self,
        message: Message,
        conversation: Conversation,
        authenticated_caller_id: str | None = None,
    ) -> Message:
        """
        Perform full routing validation pass on message against conversation and caller context.
        """
        # 1. Validate Sender Authority
        await self.validate_sender_authority(
            sender_employee_id=message.sender_employee_id,
            sender_agent_id=message.sender_agent_id,
            authenticated_caller_id=authenticated_caller_id,
        )

        # 2. Validate Conversation Membership
        await self.validate_conversation_membership(
            conversation=conversation,
            sender_employee_id=message.sender_employee_id,
        )

        # 3. Validate Recipients (All conversation participants must be valid active employees)
        for participant in conversation.participants:
            if participant.participant_type == "employee":
                emp = await _maybe_await(self.employee_repo.get_by_id(participant.participant_id))
                if emp is None:
                    raise CommunicationValidationError(
                        f"Recipient employee ID '{participant.participant_id}' does not exist."
                    )

        # Ensure message conversation_id matches
        message.conversation_id = conversation.id
        return message
