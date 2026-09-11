"""Create departments and employees tables

Revision ID: 005_create_departments_and_employees
Revises: 004_create_agent_checkpoints
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_create_departments_and_employees"
down_revision: str | None = "004_create_agent_checkpoints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_departments_code"), "departments", ["code"], unique=True)

    # 2. Create employees table
    op.create_table(
        "employees",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("employee_code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=128), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("department_id", sa.String(length=64), nullable=True),
        sa.Column("manager_id", sa.String(length=64), nullable=True),
        sa.Column("responsibilities", sa.JSON(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["manager_id"], ["employees.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_employees_employee_code"), "employees", ["employee_code"], unique=True)
    op.create_index(op.f("ix_employees_role"), "employees", ["role"], unique=False)
    op.create_index(op.f("ix_employees_agent_id"), "employees", ["agent_id"], unique=False)
    op.create_index(
        op.f("ix_employees_department_id"), "employees", ["department_id"], unique=False
    )
    op.create_index(op.f("ix_employees_manager_id"), "employees", ["manager_id"], unique=False)
    op.create_index(op.f("ix_employees_status"), "employees", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_employees_status"), table_name="employees")
    op.drop_index(op.f("ix_employees_manager_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_department_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_agent_id"), table_name="employees")
    op.drop_index(op.f("ix_employees_role"), table_name="employees")
    op.drop_index(op.f("ix_employees_employee_code"), table_name="employees")
    op.drop_table("employees")

    op.drop_index(op.f("ix_departments_code"), table_name="departments")
    op.drop_table("departments")
