"""
SQLAlchemy ORM Model for ExecutionStep persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.step import ExecutionStep, StepStatus, StepType
from src.infrastructure.database import Base


class ExecutionStepModel(Base):
    __tablename__ = "agent_run_steps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StepStatus.STARTED.value
    )
    input_data_json: Mapped[dict[str, Any]] = mapped_column(
        "input_data", JSON, nullable=False, default=dict
    )
    output_data_json: Mapped[dict[str, Any] | None] = mapped_column(
        "output_data", JSON, nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )


def step_model_to_domain(model: ExecutionStepModel) -> ExecutionStep:
    """Map SQLAlchemy ExecutionStepModel to pure Domain ExecutionStep entity."""
    return ExecutionStep(
        id=model.id,
        run_id=model.run_id,
        step_number=model.step_number,
        step_type=StepType(model.step_type),
        status=StepStatus(model.status),
        input_data=dict(model.input_data_json or {}),
        output_data=dict(model.output_data_json) if model.output_data_json is not None else None,
        error_message=model.error_message,
        started_at=model.started_at,
        completed_at=model.completed_at,
        metadata=dict(model.metadata_json or {}),
    )


def step_domain_to_model(step: ExecutionStep) -> ExecutionStepModel:
    """Map pure Domain ExecutionStep entity to SQLAlchemy ExecutionStepModel."""
    return ExecutionStepModel(
        id=step.id,
        run_id=step.run_id,
        step_number=step.step_number,
        step_type=step.step_type.value,
        status=step.status.value,
        input_data_json=step.input_data,
        output_data_json=step.output_data,
        error_message=step.error_message,
        started_at=step.started_at,
        completed_at=step.completed_at,
        metadata_json=step.metadata,
    )
