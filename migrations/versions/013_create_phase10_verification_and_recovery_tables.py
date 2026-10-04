"""Create Phase 10 Verification and Recovery tables

Revision ID: 013_create_phase10_verification_and_recovery_tables
Revises: 012_create_phase9_software_company_tables
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Verifications
    op.create_table(
        "verifications",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("outcome_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("recommended_recovery", sa.String(length=64), nullable=True),
        sa.Column("is_human_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_by_actor_id", sa.String(length=64), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verifications_task_id", "verifications", ["task_id"])
    op.create_index("ix_verifications_outcome_id", "verifications", ["outcome_id"])
    op.create_index("ix_verifications_status", "verifications", ["status"])

    # 2. Expected Outcomes
    op.create_table(
        "expected_outcomes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("rules_data", sa.JSON(), nullable=False),
        sa.Column("required_evidence_types", sa.JSON(), nullable=False),
        sa.Column("completion_conditions", sa.JSON(), nullable=False),
        sa.Column("failure_conditions", sa.JSON(), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expected_outcomes_task_id", "expected_outcomes", ["task_id"])

    # 3. Verification Evidence
    op.create_table(
        "verification_evidence",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("agent_run_id", sa.String(length=64), nullable=True),
        sa.Column("employee_id", sa.String(length=64), nullable=True),
        sa.Column("tool_execution_id", sa.String(length=64), nullable=True),
        sa.Column("artifact_id", sa.String(length=64), nullable=True),
        sa.Column("trust_level", sa.String(length=32), nullable=False, server_default="UNTRUSTED"),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("commit_sha", sa.String(length=64), nullable=True),
        sa.Column("artifact_version", sa.String(length=32), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verification_evidence_source_type", "verification_evidence", ["source_type"])
    op.create_index("ix_verification_evidence_source_id", "verification_evidence", ["source_id"])
    op.create_index("ix_verification_evidence_task_id", "verification_evidence", ["task_id"])
    op.create_index("ix_verification_evidence_workspace_id", "verification_evidence", ["workspace_id"])

    # 4. Failure Records
    op.create_table(
        "failure_records",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("verification_id", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="HIGH"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("retryable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("recoverable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("recommended_strategy", sa.String(length=64), nullable=True),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("employee_id", sa.String(length=64), nullable=True),
        sa.Column("execution_id", sa.String(length=64), nullable=True),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_failure_records_task_id", "failure_records", ["task_id"])
    op.create_index("ix_failure_records_verification_id", "failure_records", ["verification_id"])
    op.create_index("ix_failure_records_category", "failure_records", ["category"])

    # 5. Recovery Actions
    op.create_table(
        "recovery_actions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("failure_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("executed_by", sa.String(length=64), nullable=False, server_default="SYSTEM"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recovery_actions_failure_id", "recovery_actions", ["failure_id"])
    op.create_index("ix_recovery_actions_task_id", "recovery_actions", ["task_id"])
    op.create_index("ix_recovery_actions_strategy", "recovery_actions", ["strategy"])


def downgrade() -> None:
    op.drop_table("recovery_actions")
    op.drop_table("failure_records")
    op.drop_table("verification_evidence")
    op.drop_table("expected_outcomes")
    op.drop_table("verifications")
