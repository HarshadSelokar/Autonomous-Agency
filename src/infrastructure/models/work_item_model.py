"""
SQLAlchemy ORM Model for WorkItem persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.work_item import WorkItem, WorkItemStatus
from src.infrastructure.database import Base


class WorkItemModel(Base):
    __tablename__ = "work_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(2048), nullable=False)
    required_capabilities_json: Mapped[list[str]] = mapped_column(
        "required_capabilities", JSON, nullable=False, default=list
    )
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium")
    assigned_employee_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorkItemStatus.PLANNED.value, index=True
    )
    result_json: Mapped[dict[str, Any] | None] = mapped_column(
        "result", JSON, nullable=True, default=None
    )
    blocker_reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def work_item_model_to_domain(model: WorkItemModel) -> WorkItem:
    return WorkItem(
        id=model.id,
        plan_id=model.plan_id,
        title=model.title,
        description=model.description,
        required_capabilities=list(model.required_capabilities_json or []),
        priority=model.priority,
        assigned_employee_id=model.assigned_employee_id,
        status=WorkItemStatus(model.status),
        result=dict(model.result_json) if model.result_json is not None else None,
        blocker_reason=model.blocker_reason,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def work_item_domain_to_model(domain: WorkItem) -> WorkItemModel:
    return WorkItemModel(
        id=domain.id,
        plan_id=domain.plan_id,
        title=domain.title,
        description=domain.description,
        required_capabilities_json=domain.required_capabilities,
        priority=domain.priority,
        assigned_employee_id=domain.assigned_employee_id,
        status=domain.status.value,
        result_json=domain.result,
        blocker_reason=domain.blocker_reason,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
