"""
SQLAlchemy ORM Model for Message domain entity.
"""

from datetime import datetime, timezone
import json

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.message import (
    DeliveryState,
    Message,
    MessageReference,
    MessageType,
)
from src.infrastructure.database import Base


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sender_agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    sender_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    references_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    reply_to_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    delivery_state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="CREATED", index=True
    )
    acknowledgements_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


def message_domain_to_model(msg: Message) -> MessageModel:
    return MessageModel(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_employee_id=msg.sender_employee_id,
        sender_agent_id=msg.sender_agent_id,
        sender_run_id=msg.sender_run_id,
        message_type=msg.message_type.value,
        subject=msg.subject,
        content=msg.content,
        priority=msg.priority,
        references_json=json.dumps([r.to_dict() for r in msg.references]),
        reply_to_message_id=msg.reply_to_message_id,
        correlation_id=msg.correlation_id,
        delivery_state=msg.delivery_state.value,
        acknowledgements_json=json.dumps(msg.acknowledgements),
        metadata_json=json.dumps(msg.metadata),
        created_at=msg.created_at,
        updated_at=msg.updated_at,
    )


def message_model_to_domain(model: MessageModel) -> Message:
    raw_refs = json.loads(model.references_json or "[]")
    references = [MessageReference.from_dict(r) for r in raw_refs]
    raw_acks = json.loads(model.acknowledgements_json or "{}")
    raw_meta = json.loads(model.metadata_json or "{}")

    return Message(
        id=model.id,
        conversation_id=model.conversation_id,
        sender_employee_id=model.sender_employee_id,
        sender_agent_id=model.sender_agent_id,
        sender_run_id=model.sender_run_id,
        message_type=MessageType(model.message_type),
        subject=model.subject,
        content=model.content,
        priority=model.priority,
        references=references,
        reply_to_message_id=model.reply_to_message_id,
        correlation_id=model.correlation_id,
        delivery_state=DeliveryState(model.delivery_state),
        acknowledgements=raw_acks,
        metadata=raw_meta,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
