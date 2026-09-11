"""
SQLAlchemy ORM Model for AgentCheckpoint persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.checkpoint import AgentCheckpoint
from src.infrastructure.database import Base


class AgentCheckpointModel(Base):
    __tablename__ = "agent_checkpoints"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_state: Mapped[str] = mapped_column(String(32), nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False)
    context_reference_json: Mapped[dict[str, Any]] = mapped_column(
        "context_reference", JSON, nullable=False, default=dict
    )
    output_so_far_json: Mapped[dict[str, Any] | None] = mapped_column(
        "output_so_far", JSON, nullable=True
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def checkpoint_model_to_domain(model: AgentCheckpointModel) -> AgentCheckpoint:
    """Map SQLAlchemy AgentCheckpointModel to pure Domain AgentCheckpoint entity."""
    so_far = (
        dict(model.output_so_far_json) if model.output_so_far_json is not None else None
    )
    return AgentCheckpoint(
        id=model.id,
        run_id=model.run_id,
        current_state=model.current_state,
        current_step=model.current_step,
        context_reference=dict(model.context_reference_json or {}),
        output_so_far=so_far,
        metadata=dict(model.metadata_json or {}),
        timestamp=model.timestamp,
    )


def checkpoint_domain_to_model(checkpoint: AgentCheckpoint) -> AgentCheckpointModel:
    """Map pure Domain AgentCheckpoint entity to SQLAlchemy AgentCheckpointModel."""
    return AgentCheckpointModel(
        id=checkpoint.id,
        run_id=checkpoint.run_id,
        current_state=checkpoint.current_state,
        current_step=checkpoint.current_step,
        context_reference_json=checkpoint.context_reference,
        output_so_far_json=checkpoint.output_so_far,
        metadata_json=checkpoint.metadata,
        timestamp=checkpoint.timestamp,
    )
