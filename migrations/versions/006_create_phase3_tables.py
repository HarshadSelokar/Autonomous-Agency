"""Create Phase 3 objectives, plans, work_items, assignments, decisions tables

Revision ID: 006_create_phase3_tables
Revises: 005_create_departments_and_employees
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_create_phase3_tables"
down_revision: str | None = "005_create_departments_and_employees"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Objectives table
    op.create_table(
        "objectives",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requester", sa.String(length=128), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("manager_id", sa.String(length=64), nullable=True),
        sa.Column("plan_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_objectives_requester"), "objectives", ["requester"], unique=False)
    op.create_index(op.f("ix_objectives_status"), "objectives", ["status"], unique=False)
    op.create_index(op.f("ix_objectives_manager_id"), "objectives", ["manager_id"], unique=False)
    op.create_index(op.f("ix_objectives_plan_id"), "objectives", ["plan_id"], unique=False)

    # 2. Plans table
    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("manager_id", sa.String(length=64), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plans_objective_id"), "plans", ["objective_id"], unique=False)
    op.create_index(op.f("ix_plans_manager_id"), "plans", ["manager_id"], unique=False)
    op.create_index(op.f("ix_plans_status"), "plans", ["status"], unique=False)

    # 3. Work items table
    op.create_table(
        "work_items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("plan_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("assigned_employee_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("blocker_reason", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigned_employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_work_items_plan_id"), "work_items", ["plan_id"], unique=False)
    op.create_index(
        op.f("ix_work_items_assigned_employee_id"),
        "work_items",
        ["assigned_employee_id"],
        unique=False,
    )
    op.create_index(op.f("ix_work_items_status"), "work_items", ["status"], unique=False)

    # 4. Assignments table
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("work_item_id", sa.String(length=64), nullable=False),
        sa.Column("employee_id", sa.String(length=64), nullable=False),
        sa.Column("assigned_by", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by"], ["employees.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assignments_work_item_id"), "assignments", ["work_item_id"], unique=False
    )
    op.create_index(
        op.f("ix_assignments_employee_id"), "assignments", ["employee_id"], unique=False
    )
    op.create_index(
        op.f("ix_assignments_assigned_by"), "assignments", ["assigned_by"], unique=False
    )
    op.create_index(op.f("ix_assignments_status"), "assignments", ["status"], unique=False)

    # 5. Manager Decisions table
    op.create_table(
        "manager_decisions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("manager_id", sa.String(length=64), nullable=False),
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("selected_action", sa.String(length=512), nullable=False),
        sa.Column("alternatives", sa.JSON(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_manager_decisions_manager_id"), "manager_decisions", ["manager_id"], unique=False
    )
    op.create_index(
        op.f("ix_manager_decisions_objective_id"),
        "manager_decisions",
        ["objective_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_manager_decisions_decision_type"),
        "manager_decisions",
        ["decision_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("manager_decisions")
    op.drop_table("assignments")
    op.drop_table("work_items")
    op.drop_table("plans")
    op.drop_table("objectives")
