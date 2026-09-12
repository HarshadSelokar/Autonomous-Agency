"""
SQLAlchemy ORM Model for AgentRun persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.run import AgentRun, RunStatus
from src.infrastructure.database import Base


class AgentRunModel(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=RunStatus.CREATED.value)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="groq")
    model: Mapped[str] = mapped_column(
        String(128), nullable=False, default="llama-3.3-70b-versatile"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    usage_json: Mapped[dict[str, Any]] = mapped_column("usage", JSON, nullable=False, default=dict)
    result_json: Mapped[dict[str, Any] | None] = mapped_column("result", JSON, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def run_model_to_domain(model: AgentRunModel) -> AgentRun:
    """Map SQLAlchemy AgentRunModel to pure Domain AgentRun entity."""
    return AgentRun(
        id=model.id,
        agent_id=model.agent_id,
        objective=model.objective,
        status=RunStatus(model.status),
        provider=model.provider,
        model=model.model,
        started_at=model.started_at,
        completed_at=model.completed_at,
        failure_reason=model.failure_reason,
        usage=dict(model.usage_json or {}),
        result=dict(model.result_json) if model.result_json is not None else None,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def run_domain_to_model(run: AgentRun) -> AgentRunModel:
    """Map pure Domain AgentRun entity to SQLAlchemy AgentRunModel."""
    return AgentRunModel(
        id=run.id,
        agent_id=run.agent_id,
        objective=run.objective,
        status=run.status.value,
        provider=run.provider,
        model=run.model,
        started_at=run.started_at,
        completed_at=run.completed_at,
        failure_reason=run.failure_reason,
        usage_json=run.usage,
        result_json=run.result,
        metadata_json=run.metadata,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )
