"""Create Phase 9 AI Software Company tables

Revision ID: 012_create_phase9_software_company_tables
Revises: 011_create_phase8_tools_and_integrations_tables
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012_create_phase9_software_company_tables"
down_revision: str | None = "011_create_phase8_tools_and_integrations_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Software Projects
    op.create_table(
        "software_projects",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("objective_id", sa.String(length=64), nullable=False),
        sa.Column("repository_path", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("workspace_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="CREATED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_software_projects_objective", "software_projects", ["objective_id"])
    op.create_index("ix_software_projects_status", "software_projects", ["status"])

    # 2. Software Requirements
    op.create_table(
        "software_requirements",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("clarification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["software_projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_software_requirements_project", "software_requirements", ["project_id"])
    op.create_index("ix_software_requirements_status", "software_requirements", ["status"])

    # 3. Engineering Plans
    op.create_table(
        "engineering_plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("manager_employee_id", sa.String(length=64), nullable=False),
        sa.Column("architecture_overview", sa.Text(), nullable=False, server_default=""),
        sa.Column("tech_stack", sa.JSON(), nullable=False),
        sa.Column("task_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["software_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_engineering_plans_project", "engineering_plans", ["project_id"])

    # 4. Code Changes
    op.create_table(
        "code_changes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("author_employee_id", sa.String(length=64), nullable=False),
        sa.Column("agent_run_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("workspace_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("branch_name", sa.String(length=128), nullable=False, server_default="main"),
        sa.Column("files_changed", sa.JSON(), nullable=False),
        sa.Column("diff_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PROPOSED"),
        sa.Column("commit_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["software_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["author_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_code_changes_project", "code_changes", ["project_id"])
    op.create_index("ix_code_changes_task", "code_changes", ["task_id"])
    op.create_index("ix_code_changes_status", "code_changes", ["status"])

    # 5. Code Reviews
    op.create_table(
        "code_reviews",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("change_id", sa.String(length=64), nullable=False),
        sa.Column("reviewer_employee_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("findings", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["change_id"], ["code_changes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_code_reviews_change", "code_reviews", ["change_id"])
    op.create_index("ix_code_reviews_status", "code_reviews", ["status"])

    # 6. Test Runs
    op.create_table(
        "test_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("worker_employee_id", sa.String(length=64), nullable=False),
        sa.Column("agent_run_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("workspace_id", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("command", sa.String(length=512), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_reference", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("evidence_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="RUNNING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["software_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["worker_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_test_runs_project", "test_runs", ["project_id"])
    op.create_index("ix_test_runs_task", "test_runs", ["task_id"])
    op.create_index("ix_test_runs_status", "test_runs", ["status"])

    # 7. Software Defects
    op.create_table(
        "software_defects",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("reproduction_steps", sa.Text(), nullable=False, server_default=""),
        sa.Column("originating_task_id", sa.String(length=64), nullable=True),
        sa.Column("fix_task_id", sa.String(length=64), nullable=True),
        sa.Column("assigned_employee_id", sa.String(length=64), nullable=True),
        sa.Column("verification_test_run_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["software_projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_software_defects_project", "software_defects", ["project_id"])
    op.create_index("ix_software_defects_status", "software_defects", ["status"])

    # 8. Software Deliveries
    op.create_table(
        "software_deliveries",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("commit_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("requested_by_employee_id", sa.String(length=64), nullable=False),
        sa.Column("approved_by_employee_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("evidence_summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["software_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_software_deliveries_project", "software_deliveries", ["project_id"])
    op.create_index("ix_software_deliveries_status", "software_deliveries", ["status"])


def downgrade() -> None:
    op.drop_table("software_deliveries")
    op.drop_table("software_defects")
    op.drop_table("test_runs")
    op.drop_table("code_reviews")
    op.drop_table("code_changes")
    op.drop_table("engineering_plans")
    op.drop_table("software_requirements")
    op.drop_table("software_projects")
