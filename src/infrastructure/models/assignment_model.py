"""
SQLAlchemy ORM Model for Assignment persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.assignment import Assignment, AssignmentStatus
from src.infrastructure.database import Base


class AssignmentModel(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    work_item_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_by: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AssignmentStatus.ACTIVE.value, index=True
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def assignment_model_to_domain(model: AssignmentModel) -> Assignment:
    return Assignment(
        id=model.id,
        work_item_id=model.work_item_id,
        employee_id=model.employee_id,
        assigned_by=model.assigned_by,
        reason=model.reason,
        status=AssignmentStatus(model.status),
        metadata=dict(model.metadata_json or {}),
        assigned_at=model.assigned_at,
        updated_at=model.updated_at,
    )


def assignment_domain_to_model(domain: Assignment) -> AssignmentModel:
    return AssignmentModel(
        id=domain.id,
        work_item_id=domain.work_item_id,
        employee_id=domain.employee_id,
        assigned_by=domain.assigned_by,
        reason=domain.reason,
        status=domain.status.value,
        metadata_json=domain.metadata,
        assigned_at=domain.assigned_at,
        updated_at=domain.updated_at,
    )
