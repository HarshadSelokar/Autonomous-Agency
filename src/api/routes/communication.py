"""
FastAPI Router for Phase 5 Communication & Collaboration REST API endpoints.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.communication_schemas import (
    AcknowledgeMessageRequest,
    AddParticipantRequest,
    ConversationResponse,
    CreateConversationRequest,
    EscalateBlockerRequest,
    MessageResponse,
    ReportBlockerRequest,
    SendMessageRequest,
)
from src.application.communication_service import CommunicationService
from src.application.message_delivery_service import MessageDeliveryService
from src.application.message_router import (
    CommunicationAuthorizationError,
    CommunicationValidationError,
    MessageRouter,
)
from src.domain.conversation import ConversationParticipant, ConversationType
from src.domain.exceptions import DomainError
from src.domain.message import MessageReference, MessageType
from src.infrastructure.database import get_db
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.conversation_repository import (
    ConversationNotFoundError,
    SQLAlchemyConversationRepository,
)
from src.infrastructure.repositories.employee_repository import (
    SQLAlchemyEmployeeRepository,
)
from src.infrastructure.repositories.message_repository import (
    MessageNotFoundError,
    SQLAlchemyMessageRepository,
)
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository

router = APIRouter(tags=["Communication"])


def get_communication_service(session: AsyncSession = Depends(get_db)) -> CommunicationService:
    conv_repo = SQLAlchemyConversationRepository(session)
    msg_repo = SQLAlchemyMessageRepository(session)
    outbox_repo = SQLAlchemyOutboxRepository(session)
    emp_repo = SQLAlchemyEmployeeRepository(session)
    agent_repo = SQLAlchemyAgentRepository(session)

    message_router = MessageRouter(
        employee_repository=emp_repo,
        agent_repository=agent_repo,
        conversation_repository=conv_repo,
    )
    delivery_service = MessageDeliveryService(
        message_repository=msg_repo,
        outbox_repository=outbox_repo,
    )
    return CommunicationService(
        conversation_repository=conv_repo,
        message_repository=msg_repo,
        message_router=message_router,
        message_delivery_service=delivery_service,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
async def create_conversation(
    req: CreateConversationRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        conv = await service.create_conversation(
            title=req.title,
            conversation_type=ConversationType(req.conversation_type),
            created_by_employee_id=req.created_by_employee_id,
            participant_employee_ids=req.participant_employee_ids,
            related_objective_id=req.related_objective_id,
            related_plan_id=req.related_plan_id,
            related_task_id=req.related_task_id,
            related_project_id=req.related_project_id,
            metadata=req.metadata,
        )
        return conv.to_dict()
    except DomainError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation by ID",
)
async def get_conversation(
    conversation_id: str,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        conv = await service.conversation_repo.get_by_id(conversation_id)
        return conv.to_dict()
    except ConversationNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    summary="List all conversations",
)
async def list_conversations(
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    convs = await service.conversation_repo.get_all()
    return [c.to_dict() for c in convs]


@router.post(
    "/conversations/{conversation_id}/participants",
    response_model=ConversationResponse,
    summary="Add a participant to conversation",
)
async def add_participant(
    conversation_id: str,
    req: AddParticipantRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        conv = await service.conversation_repo.get_by_id(conversation_id)
        conv.add_participant(
            ConversationParticipant(
                participant_id=req.participant_id,
                participant_type=req.participant_type,
                role=req.role,
            )
        )
        saved = await service.conversation_repo.save(conv)
        return saved.to_dict()
    except ConversationNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except DomainError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.delete(
    "/conversations/{conversation_id}/participants/{participant_id}",
    response_model=ConversationResponse,
    summary="Remove a participant from conversation",
)
async def remove_participant(
    conversation_id: str,
    participant_id: str,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        conv = await service.conversation_repo.get_by_id(conversation_id)
        conv.remove_participant(participant_id)
        saved = await service.conversation_repo.save(conv)
        return saved.to_dict()
    except ConversationNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message in a conversation",
)
async def send_message_in_conversation(
    conversation_id: str,
    req: SendMessageRequest,
    x_authenticated_employee_id: str | None = Header(None),
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        refs = [
            MessageReference(
                reference_type=r.reference_type, reference_id=r.reference_id, metadata=r.metadata
            )
            for r in req.references
        ]
        msg = await service.send_message(
            sender_employee_id=req.sender_employee_id,
            conversation_id=conversation_id,
            message_type=MessageType(req.message_type),
            subject=req.subject,
            content=req.content,
            priority=req.priority,
            references=refs,
            reply_to_message_id=req.reply_to_message_id,
            sender_agent_id=req.sender_agent_id,
            sender_run_id=req.sender_run_id,
            authenticated_caller_id=x_authenticated_employee_id,
            metadata=req.metadata,
        )
        return msg.to_dict()
    except (CommunicationAuthorizationError, CommunicationValidationError) as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except DomainError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="Get all messages in a conversation",
)
async def list_messages_in_conversation(
    conversation_id: str,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    msgs = await service.message_repo.get_by_conversation_id(conversation_id)
    return [m.to_dict() for m in msgs]


@router.get(
    "/messages/{message_id}",
    response_model=MessageResponse,
    summary="Get message by ID",
)
async def get_message(
    message_id: str,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        msg = await service.message_repo.get_by_id(message_id)
        return msg.to_dict()
    except MessageNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post(
    "/messages/{message_id}/acknowledge",
    response_model=MessageResponse,
    summary="Acknowledge a message",
)
async def acknowledge_message(
    message_id: str,
    req: AcknowledgeMessageRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        msg = await service.delivery_service.acknowledge_message(
            message_id=message_id, participant_id=req.participant_id
        )
        return msg.to_dict()
    except MessageNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post(
    "/tasks/{task_id}/blockers",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a task blocker to manager",
)
async def report_task_blocker(
    task_id: str,
    req: ReportBlockerRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        msg = await service.report_blocker(
            sender_employee_id=req.sender_employee_id,
            task_id=task_id,
            blocker_description=req.blocker_description,
            manager_employee_id=req.manager_employee_id,
            sender_agent_id=req.sender_agent_id,
            sender_run_id=req.sender_run_id,
        )
        return msg.to_dict()
    except DomainError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post(
    "/tasks/{task_id}/escalations",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Escalate an unresolved task blocker up the manager hierarchy",
)
async def escalate_task_blocker(
    task_id: str,
    req: EscalateBlockerRequest,
    service: CommunicationService = Depends(get_communication_service),
) -> Any:
    try:
        msg = await service.escalate_blocker(
            sender_manager_id=req.sender_manager_id,
            task_id=task_id,
            original_blocker_message_id=req.original_blocker_message_id,
            higher_manager_id=req.higher_manager_id,
            escalation_reason=req.escalation_reason,
        )
        return msg.to_dict()
    except DomainError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
