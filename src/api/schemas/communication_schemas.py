"""
Pydantic Request & Response Schemas for Communication REST APIs.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ConversationParticipantSchema(BaseModel):
    participant_id: str
    participant_type: str = "employee"
    role: str = "member"
    joined_at: str | None = None


class CreateConversationRequest(BaseModel):
    title: str = Field(..., description="Conversation title")
    conversation_type: str = Field(
        "DIRECT", description="DIRECT, TEAM, TASK, OBJECTIVE, MANAGER, ESCALATION"
    )
    created_by_employee_id: str
    participant_employee_ids: list[str] = Field(default_factory=list)
    related_objective_id: str | None = None
    related_plan_id: str | None = None
    related_task_id: str | None = None
    related_project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    id: str
    title: str
    conversation_type: str
    created_by_employee_id: str
    participants: list[ConversationParticipantSchema]
    related_objective_id: str | None = None
    related_plan_id: str | None = None
    related_task_id: str | None = None
    related_project_id: str | None = None
    status: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class AddParticipantRequest(BaseModel):
    participant_id: str
    participant_type: str = "employee"
    role: str = "member"


class MessageReferenceSchema(BaseModel):
    reference_type: str
    reference_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    sender_employee_id: str
    message_type: str = "INFORMATION"
    subject: str = ""
    content: str
    priority: str = "medium"
    references: list[MessageReferenceSchema] = Field(default_factory=list)
    reply_to_message_id: str | None = None
    sender_agent_id: str | None = None
    sender_run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_employee_id: str
    sender_agent_id: str | None = None
    sender_run_id: str | None = None
    message_type: str
    subject: str
    content: str
    priority: str
    references: list[MessageReferenceSchema]
    reply_to_message_id: str | None = None
    correlation_id: str
    delivery_state: str
    acknowledgements: dict[str, str]
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class ReportBlockerRequest(BaseModel):
    sender_employee_id: str
    blocker_description: str
    manager_employee_id: str
    sender_agent_id: str | None = None
    sender_run_id: str | None = None


class EscalateBlockerRequest(BaseModel):
    sender_manager_id: str
    original_blocker_message_id: str
    higher_manager_id: str
    escalation_reason: str


class AcknowledgeMessageRequest(BaseModel):
    participant_id: str
