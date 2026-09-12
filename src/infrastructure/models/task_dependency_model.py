"""
SQLAlchemy ORM Model for TaskDependency persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.task_dependency import DependencyStatus, DependencyType, TaskDependency
from src.infrastructure.database import Base


class TaskDependencyModel(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "predecessor_task_id",
            "successor_task_id",
            name="uq_task_dependency_edge",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    predecessor_task_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    successor_task_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DependencyType.BLOCKING.value
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=DependencyStatus.ACTIVE.value, index=True
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def task_dependency_model_to_domain(model: TaskDependencyModel) -> TaskDependency:
    return TaskDependency(
        id=model.id,
        predecessor_task_id=model.predecessor_task_id,
        successor_task_id=model.successor_task_id,
        dependency_type=DependencyType(model.dependency_type),
        status=DependencyStatus(model.status),
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def task_dependency_domain_to_model(domain: TaskDependency) -> TaskDependencyModel:
    return TaskDependencyModel(
        id=domain.id,
        predecessor_task_id=domain.predecessor_task_id,
        successor_task_id=domain.successor_task_id,
        dependency_type=domain.dependency_type.value,
        status=domain.status.value,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
