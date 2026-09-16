"""
SQLAlchemy ORM Model for Conversation domain entity.
"""

import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.conversation import (
    Conversation,
    ConversationParticipant,
    ConversationType,
)
from src.infrastructure.database import Base


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    conversation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_by_employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    participants_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    related_objective_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    related_plan_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    related_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    related_project_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def conversation_domain_to_model(conv: Conversation) -> ConversationModel:
    return ConversationModel(
        id=conv.id,
        title=conv.title,
        conversation_type=conv.conversation_type.value,
        created_by_employee_id=conv.created_by_employee_id,
        participants_json=json.dumps([p.to_dict() for p in conv.participants]),
        related_objective_id=conv.related_objective_id,
        related_plan_id=conv.related_plan_id,
        related_task_id=conv.related_task_id,
        related_project_id=conv.related_project_id,
        status=conv.status,
        metadata_json=json.dumps(conv.metadata),
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


def conversation_model_to_domain(model: ConversationModel) -> Conversation:
    raw_parts = json.loads(model.participants_json or "[]")
    participants = [ConversationParticipant.from_dict(p) for p in raw_parts]
    raw_meta = json.loads(model.metadata_json or "{}")

    return Conversation(
        id=model.id,
        title=model.title,
        conversation_type=ConversationType(model.conversation_type),
        created_by_employee_id=model.created_by_employee_id,
        participants=participants,
        related_objective_id=model.related_objective_id,
        related_plan_id=model.related_plan_id,
        related_task_id=model.related_task_id,
        related_project_id=model.related_project_id,
        status=model.status,
        metadata=raw_meta,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
