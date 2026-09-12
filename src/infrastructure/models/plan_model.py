"""
SQLAlchemy ORM Model for Plan persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.plan import Plan, PlanStatus
from src.infrastructure.database import Base
from src.infrastructure.models.work_item_model import (
    WorkItemModel,
    work_item_domain_to_model,
    work_item_model_to_domain,
)


class PlanModel(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    objective_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False, index=True
    )
    manager_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assumptions_json: Mapped[list[str]] = mapped_column(
        "assumptions", JSON, nullable=False, default=list
    )
    goals_json: Mapped[list[str]] = mapped_column(
        "goals", JSON, nullable=False, default=list
    )
    required_capabilities_json: Mapped[list[str]] = mapped_column(
        "required_capabilities", JSON, nullable=False, default=list
    )
    risks_json: Mapped[list[str]] = mapped_column(
        "risks", JSON, nullable=False, default=list
    )
    constraints_json: Mapped[list[str]] = mapped_column(
        "constraints", JSON, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=PlanStatus.DRAFT.value, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def plan_model_to_domain(
    model: PlanModel, work_item_models: list[WorkItemModel] | None = None
) -> Plan:
    work_items = [work_item_model_to_domain(w) for w in (work_item_models or [])]
    return Plan(
        id=model.id,
        objective_id=model.objective_id,
        manager_id=model.manager_id,
        assumptions=list(model.assumptions_json or []),
        goals=list(model.goals_json or []),
        work_items=work_items,
        required_capabilities=list(model.required_capabilities_json or []),
        risks=list(model.risks_json or []),
        constraints=list(model.constraints_json or []),
        status=PlanStatus(model.status),
        version=model.version,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def plan_domain_to_model(domain: Plan) -> tuple[PlanModel, list[WorkItemModel]]:
    plan_model = PlanModel(
        id=domain.id,
        objective_id=domain.objective_id,
        manager_id=domain.manager_id,
        assumptions_json=domain.assumptions,
        goals_json=domain.goals,
        required_capabilities_json=domain.required_capabilities,
        risks_json=domain.risks,
        constraints_json=domain.constraints,
        status=domain.status.value,
        version=domain.version,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
    work_item_models = [work_item_domain_to_model(w) for w in domain.work_items]
    return plan_model, work_item_models
