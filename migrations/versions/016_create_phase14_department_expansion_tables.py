"""Create Phase 14 Department expansion, request, handoff, contract, and metrics tables

Revision ID: 016_create_phase14_department_expansion_tables
Revises: 015_create_phase13_office_projection_tables
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "016_create_phase14_department_expansion_tables"
down_revision: str | None = "015_create_phase13_office_projection_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Department Requests
    op.create_table(
        "department_requests",
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("requester_department_id", sa.String(length=64), nullable=False),
        sa.Column("receiving_department_id", sa.String(length=64), nullable=False),
        sa.Column("requester_employee_id", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("requested_outcome", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="REQUESTED"),
        sa.Column("accountable_manager_id", sa.String(length=64), nullable=True),
        sa.Column("delivery_owner_employee_id", sa.String(length=64), nullable=True),
        sa.Column("target_completion_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("required_capabilities", sa.JSON(), nullable=False),
        sa.Column("related_objective_id", sa.String(length=64), nullable=True),
        sa.Column("related_project_id", sa.String(length=64), nullable=True),
        sa.Column("governance_request_id", sa.String(length=64), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index("ix_department_requests_requester_dept", "department_requests", ["requester_department_id"])
    op.create_index("ix_department_requests_receiving_dept", "department_requests", ["receiving_department_id"])
    op.create_index("ix_department_requests_status", "department_requests", ["status"])

    # 2. Department Handoffs
    op.create_table(
        "department_handoffs",
        sa.Column("handoff_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("sender_department_id", sa.String(length=64), nullable=False),
        sa.Column("receiving_department_id", sa.String(length=64), nullable=False),
        sa.Column("sender_employee_id", sa.String(length=64), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("receiver_employee_id", sa.String(length=64), nullable=True),
        sa.Column("artifact_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING_VERIFICATION"),
        sa.Column("verification_id", sa.String(length=64), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("handoff_id"),
    )
    op.create_index("ix_department_handoffs_request_id", "department_handoffs", ["request_id"])

    # 3. Department Service Contracts
    op.create_table(
        "department_service_contracts",
        sa.Column("contract_id", sa.String(length=64), nullable=False),
        sa.Column("provider_department_id", sa.String(length=64), nullable=False),
        sa.Column("consumer_department_id", sa.String(length=64), nullable=False),
        sa.Column("service_type", sa.String(length=128), nullable=False),
        sa.Column("required_input_schema", sa.JSON(), nullable=False),
        sa.Column("expected_output_schema", sa.JSON(), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False),
        sa.Column("sla_seconds", sa.Integer(), nullable=False, server_default="86400"),
        sa.Column("requires_governance_approval", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("contract_id"),
    )

    # 4. Department Metrics
    op.create_table(
        "department_metrics",
        sa.Column("department_id", sa.String(length=64), nullable=False),
        sa.Column("active_task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_task_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incoming_request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outgoing_request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verification_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recovery_attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("escalation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("health", sa.String(length=32), nullable=False, server_default="HEALTHY"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("department_id"),
    )


def downgrade() -> None:
    op.drop_table("department_metrics")
    op.drop_table("department_service_contracts")
    op.drop_table("department_handoffs")
    op.drop_table("department_requests")
