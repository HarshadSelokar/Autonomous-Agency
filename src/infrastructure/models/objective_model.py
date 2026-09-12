"""
SQLAlchemy ORM Model for Objective persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.objective import Objective, ObjectiveStatus
from src.infrastructure.database import Base


class ObjectiveModel(Base):
    __tablename__ = "objectives"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(2048), nullable=False)
    requester: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    constraints_json: Mapped[list[str]] = mapped_column(
        "constraints", JSON, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ObjectiveStatus.RECEIVED.value, index=True
    )
    manager_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def objective_model_to_domain(model: ObjectiveModel) -> Objective:
    return Objective(
        id=model.id,
        title=model.title,
        description=model.description,
        requester=model.requester,
        priority=model.priority,
        constraints=list(model.constraints_json or []),
        status=ObjectiveStatus(model.status),
        manager_id=model.manager_id,
        plan_id=model.plan_id,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def objective_domain_to_model(domain: Objective) -> ObjectiveModel:
    return ObjectiveModel(
        id=domain.id,
        title=domain.title,
        description=domain.description,
        requester=domain.requester,
        priority=domain.priority,
        constraints_json=domain.constraints,
        status=domain.status.value,
        manager_id=domain.manager_id,
        plan_id=domain.plan_id,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
