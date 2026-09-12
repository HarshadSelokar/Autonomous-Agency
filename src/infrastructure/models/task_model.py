"""
SQLAlchemy ORM Model for Task persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.task import BlockReason, Task, TaskStatus
from src.infrastructure.database import Base


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plan_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    objective_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    work_item_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_task_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(4096), nullable=False)
    required_capabilities_json: Mapped[list[str]] = mapped_column(
        "required_capabilities", JSON, nullable=False, default=list
    )
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=TaskStatus.CREATED.value, index=True
    )
    assigned_employee_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assignment_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    execution_run_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    block_reasons_json: Mapped[list[str]] = mapped_column(
        "block_reasons", JSON, nullable=False, default=list
    )
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


def task_model_to_domain(model: TaskModel) -> Task:
    block_reasons = [BlockReason(r) for r in (model.block_reasons_json or [])]
    return Task(
        id=model.id,
        plan_id=model.plan_id,
        title=model.title,
        description=model.description,
        objective_id=model.objective_id,
        work_item_id=model.work_item_id,
        parent_task_id=model.parent_task_id,
        required_capabilities=list(model.required_capabilities_json or []),
        priority=model.priority,
        status=TaskStatus(model.status),
        assigned_employee_id=model.assigned_employee_id,
        assignment_id=model.assignment_id,
        execution_run_id=model.execution_run_id,
        retry_count=model.retry_count,
        max_retries=model.max_retries,
        block_reasons=block_reasons,
        result=model.result_json,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def task_domain_to_model(domain: Task) -> TaskModel:
    return TaskModel(
        id=domain.id,
        plan_id=domain.plan_id,
        objective_id=domain.objective_id,
        work_item_id=domain.work_item_id,
        parent_task_id=domain.parent_task_id,
        title=domain.title,
        description=domain.description,
        required_capabilities_json=domain.required_capabilities,
        priority=domain.priority,
        status=domain.status.value,
        assigned_employee_id=domain.assigned_employee_id,
        assignment_id=domain.assignment_id,
        execution_run_id=domain.execution_run_id,
        retry_count=domain.retry_count,
        max_retries=domain.max_retries,
        block_reasons_json=[br.value for br in domain.block_reasons],
        result_json=domain.result,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
