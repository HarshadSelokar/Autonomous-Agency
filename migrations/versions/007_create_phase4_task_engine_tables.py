"""Create Phase 4 tasks and task_dependencies tables

Revision ID: 007_create_phase4_task_engine_tables
Revises: 006_create_phase3_tables
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("plan_id", sa.String(length=64), nullable=False),
        sa.Column("objective_id", sa.String(length=64), nullable=True),
        sa.Column("work_item_id", sa.String(length=64), nullable=True),
        sa.Column("parent_task_id", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=4096), nullable=False),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CREATED"),
        sa.Column("assigned_employee_id", sa.String(length=64), nullable=True),
        sa.Column("assignment_id", sa.String(length=64), nullable=True),
        sa.Column("execution_run_id", sa.String(length=64), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("block_reasons", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["execution_run_id"], ["agent_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_plan_id"), "tasks", ["plan_id"], unique=False)
    op.create_index(op.f("ix_tasks_objective_id"), "tasks", ["objective_id"], unique=False)
    op.create_index(op.f("ix_tasks_work_item_id"), "tasks", ["work_item_id"], unique=False)
    op.create_index(op.f("ix_tasks_parent_task_id"), "tasks", ["parent_task_id"], unique=False)
    op.create_index(op.f("ix_tasks_priority"), "tasks", ["priority"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(
        op.f("ix_tasks_assigned_employee_id"), "tasks", ["assigned_employee_id"], unique=False
    )
    op.create_index(op.f("ix_tasks_assignment_id"), "tasks", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_tasks_execution_run_id"), "tasks", ["execution_run_id"], unique=False)

    # 2. Task dependencies table
    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("predecessor_task_id", sa.String(length=64), nullable=False),
        sa.Column("successor_task_id", sa.String(length=64), nullable=False),
        sa.Column(
            "dependency_type", sa.String(length=32), nullable=False, server_default="BLOCKING"
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["predecessor_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["successor_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "predecessor_task_id", "successor_task_id", name="uq_task_dependency_edge"
        ),
    )
    op.create_index(
        op.f("ix_task_dependencies_predecessor_task_id"),
        "task_dependencies",
        ["predecessor_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_dependencies_successor_task_id"),
        "task_dependencies",
        ["successor_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_task_dependencies_status"), "task_dependencies", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_table("task_dependencies")
    op.drop_table("tasks")
