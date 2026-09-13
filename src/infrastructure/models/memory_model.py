"""
SQLAlchemy ORM Model for MemoryEntry persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryProvenance,
    MemoryScope,
    MemoryStatus,
    MemoryType,
)
from src.infrastructure.database import Base


class MemoryModel(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    memory_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    authority: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    provenance: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    objective_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="SET NULL"), nullable=True
    )
    plan_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    task_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    employee_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    agent_run_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    meeting_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True
    )
    decision_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True
    )
    artifact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_memory_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("memories.id", ondelete="SET NULL"), nullable=True
    )
    embedding_json: Mapped[list[float] | None] = mapped_column("embedding", JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="ACTIVE", index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def memory_model_to_domain(model: MemoryModel) -> MemoryEntry:
    return MemoryEntry(
        id=model.id,
        memory_type=MemoryType(model.memory_type),
        scope=MemoryScope(model.scope),
        owner_id=model.owner_id,
        content=model.content,
        summary=model.summary,
        authority=MemoryAuthority(model.authority),
        confidence=model.confidence,
        provenance=MemoryProvenance(model.provenance),
        source_id=model.source_id,
        objective_id=model.objective_id,
        plan_id=model.plan_id,
        task_id=model.task_id,
        employee_id=model.employee_id,
        agent_run_id=model.agent_run_id,
        meeting_id=model.meeting_id,
        decision_id=model.decision_id,
        artifact_id=model.artifact_id,
        previous_memory_id=model.previous_memory_id,
        embedding=list(model.embedding_json) if model.embedding_json else None,
        status=MemoryStatus(model.status),
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def memory_domain_to_model(domain: MemoryEntry) -> MemoryModel:
    return MemoryModel(
        id=domain.id,
        memory_type=domain.memory_type.value,
        scope=domain.scope.value,
        owner_id=domain.owner_id,
        content=domain.content,
        summary=domain.summary,
        authority=domain.authority.value,
        confidence=domain.confidence,
        provenance=domain.provenance.value,
        source_id=domain.source_id,
        objective_id=domain.objective_id,
        plan_id=domain.plan_id,
        task_id=domain.task_id,
        employee_id=domain.employee_id,
        agent_run_id=domain.agent_run_id,
        meeting_id=domain.meeting_id,
        decision_id=domain.decision_id,
        artifact_id=domain.artifact_id,
        previous_memory_id=domain.previous_memory_id,
        embedding_json=domain.embedding,
        status=domain.status.value,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
