"""Create Phase 8 tools, tool_executions, tool_approvals, and tool_evidence tables

Revision ID: 011_create_phase8_tools_and_integrations_tables
Revises: 010_create_phase7_memory_workspace_artifact_tables
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011_create_phase8_tools_and_integrations_tables"
down_revision: str | None = "010_create_phase7_memory_workspace_artifact_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tools table
    op.create_table(
        "tools",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="INTEGRATION"),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="LOW"),
        sa.Column("permission_mode", sa.String(length=32), nullable=False, server_default="AUTO"),
        sa.Column("provider_name", sa.String(length=64), nullable=False, server_default="internal"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("timeout_seconds", sa.Float(), nullable=False, server_default="30.0"),
        sa.Column("retry_limit", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_idempotent", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tools_category", "tools", ["category"])
    op.create_index("ix_tools_status", "tools", ["status"])

    # 2. Tool Executions table
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("tool_id", sa.String(length=64), nullable=False),
        sa.Column("tool_version", sa.String(length=32), nullable=False, server_default="1.0.0"),
        sa.Column("capability", sa.String(length=64), nullable=False),
        sa.Column("actor_employee_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("agent_run_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("approval_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="REQUESTED"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tool_executions_tool", "tool_executions", ["tool_id"])
    op.create_index("ix_tool_executions_actor", "tool_executions", ["actor_employee_id"])
    op.create_index("ix_tool_executions_status", "tool_executions", ["status"])

    # 3. Tool Approvals table
    op.create_table(
        "tool_approvals",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("tool_id", sa.String(length=64), nullable=False),
        sa.Column("capability", sa.String(length=64), nullable=False),
        sa.Column("requester_employee_id", sa.String(length=64), nullable=False),
        sa.Column("approver_employee_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["execution_id"], ["tool_executions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_tool_approvals_execution", "tool_approvals", ["execution_id"])
    op.create_index("ix_tool_approvals_status", "tool_approvals", ["status"])

    # 4. Tool Evidence table
    op.create_table(
        "tool_evidence",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("tool_id", sa.String(length=64), nullable=False),
        sa.Column("capability", sa.String(length=64), nullable=False),
        sa.Column("actor_employee_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("agent_run_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("approval_id", sa.String(length=64), nullable=True),
        sa.Column("artifact_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["execution_id"], ["tool_executions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tool_evidence_execution", "tool_evidence", ["execution_id"])


def downgrade() -> None:
    op.drop_table("tool_evidence")
    op.drop_table("tool_approvals")
    op.drop_table("tool_executions")
    op.drop_table("tools")
