"""
SQLAlchemy ORM Model for ManagerDecision persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.decision import DecisionType, ManagerDecision
from src.infrastructure.database import Base


class ManagerDecisionModel(Base):
    __tablename__ = "manager_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    manager_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    objective_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reasoning_summary: Mapped[str] = mapped_column(String(2048), nullable=False)
    selected_action: Mapped[str] = mapped_column(String(512), nullable=False)
    alternatives_json: Mapped[list[str]] = mapped_column(
        "alternatives", JSON, nullable=False, default=list
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def decision_model_to_domain(model: ManagerDecisionModel) -> ManagerDecision:
    return ManagerDecision(
        id=model.id,
        manager_id=model.manager_id,
        objective_id=model.objective_id,
        decision_type=DecisionType(model.decision_type),
        reasoning_summary=model.reasoning_summary,
        selected_action=model.selected_action,
        alternatives=list(model.alternatives_json or []),
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
    )


def decision_domain_to_model(domain: ManagerDecision) -> ManagerDecisionModel:
    return ManagerDecisionModel(
        id=domain.id,
        manager_id=domain.manager_id,
        objective_id=domain.objective_id,
        decision_type=domain.decision_type.value,
        reasoning_summary=domain.reasoning_summary,
        selected_action=domain.selected_action,
        alternatives_json=domain.alternatives,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
    )
