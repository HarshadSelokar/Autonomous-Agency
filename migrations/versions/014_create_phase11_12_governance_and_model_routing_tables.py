"""Create Phase 11 Governance and Phase 12 Model Routing tables

Revision ID: 014_create_phase11_12_governance_and_model_routing_tables
Revises: 013_create_phase10_verification_and_recovery_tables
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "014_create_phase11_12_governance_and_model_routing_tables"
down_revision: str | None = "013_create_phase10_verification_and_recovery_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Governance Policies
    op.create_table(
        "governance_policies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False, server_default="COMPANY"),
        sa.Column("scope_id", sa.String(length=64), nullable=True),
        sa.Column("level", sa.String(length=32), nullable=False, server_default="COMPANY"),
        sa.Column("rules_data", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_governance_policies_scope", "governance_policies", ["scope"])
    op.create_index("ix_governance_policies_scope_id", "governance_policies", ["scope_id"])
    op.create_index("ix_governance_policies_level", "governance_policies", ["level"])

    # 2. Governance Approval Requests
    op.create_table(
        "governance_approval_requests",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("action_target", sa.String(length=256), nullable=False),
        sa.Column("requested_by_actor_id", sa.String(length=64), nullable=False),
        sa.Column("requested_by_employee_id", sa.String(length=64), nullable=True),
        sa.Column("requested_by_agent_id", sa.String(length=64), nullable=True),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("risk_level", sa.String(length=32), nullable=False, server_default="HIGH"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("required_approver_roles", sa.JSON(), nullable=False),
        sa.Column("prohibit_self_approval", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("approved_by_actor_id", sa.String(length=64), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_governance_approval_requests_action_type", "governance_approval_requests", ["action_type"])
    op.create_index("ix_governance_approval_requests_requested_by_actor_id", "governance_approval_requests", ["requested_by_actor_id"])
    op.create_index("ix_governance_approval_requests_task_id", "governance_approval_requests", ["task_id"])
    op.create_index("ix_governance_approval_requests_project_id", "governance_approval_requests", ["project_id"])
    op.create_index("ix_governance_approval_requests_status", "governance_approval_requests", ["status"])

    # 3. Human Interventions
    op.create_table(
        "human_interventions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("intervention_type", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_human_interventions_intervention_type", "human_interventions", ["intervention_type"])
    op.create_index("ix_human_interventions_scope", "human_interventions", ["scope"])
    op.create_index("ix_human_interventions_scope_id", "human_interventions", ["scope_id"])
    op.create_index("ix_human_interventions_actor_id", "human_interventions", ["actor_id"])

    # 4. Emergency Stops
    op.create_table(
        "emergency_stops",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("activated_by_actor_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emergency_stops_scope", "emergency_stops", ["scope"])
    op.create_index("ix_emergency_stops_scope_id", "emergency_stops", ["scope_id"])
    op.create_index("ix_emergency_stops_is_active", "emergency_stops", ["is_active"])

    # 5. Governance Overrides
    op.create_table(
        "governance_overrides",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("policy_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("previous_autonomy_level", sa.String(length=32), nullable=False),
        sa.Column("override_autonomy_level", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_governance_overrides_action_id", "governance_overrides", ["action_id"])

    # 6. Policy Violations
    op.create_table(
        "policy_violations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("policy_id", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="HIGH"),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_policy_violations_category", "policy_violations", ["category"])
    op.create_index("ix_policy_violations_actor_id", "policy_violations", ["actor_id"])

    # 7. Model Profiles
    op.create_table(
        "model_profiles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("context_window_tokens", sa.Integer(), nullable=False, server_default="128000"),
        sa.Column("cost_per_1k_input_tokens", sa.Float(), nullable=False, server_default="0.001"),
        sa.Column("cost_per_1k_output_tokens", sa.Float(), nullable=False, server_default="0.002"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="200"),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_approved_for_production", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_profiles_provider_name", "model_profiles", ["provider_name"])
    op.create_index("ix_model_profiles_model_name", "model_profiles", ["model_name"])
    op.create_index("ix_model_profiles_is_active", "model_profiles", ["is_active"])

    # 8. Model Selection Decisions
    op.create_table(
        "model_selection_decisions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("selected_model_id", sa.String(length=64), nullable=False),
        sa.Column("selected_provider_name", sa.String(length=64), nullable=False),
        sa.Column("strategy_used", sa.String(length=64), nullable=False),
        sa.Column("candidate_model_ids", sa.JSON(), nullable=False),
        sa.Column("rejected_candidates", sa.JSON(), nullable=False),
        sa.Column("score_breakdown", sa.JSON(), nullable=False),
        sa.Column("is_fallback", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_selection_decisions_request_id", "model_selection_decisions", ["request_id"])
    op.create_index("ix_model_selection_decisions_task_id", "model_selection_decisions", ["task_id"])
    op.create_index("ix_model_selection_decisions_selected_model_id", "model_selection_decisions", ["selected_model_id"])

    # 9. Model Provider Health
    op.create_table(
        "model_provider_health",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("error_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("latency_p95_ms", sa.Integer(), nullable=False, server_default="250"),
        sa.Column("rate_limit_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_reason", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_provider_health_provider_name", "model_provider_health", ["provider_name"])
    op.create_index("ix_model_provider_health_model_id", "model_provider_health", ["model_id"])
    op.create_index("ix_model_provider_health_is_healthy", "model_provider_health", ["is_healthy"])


def downgrade() -> None:
    op.drop_table("model_provider_health")
    op.drop_table("model_selection_decisions")
    op.drop_table("model_profiles")
    op.drop_table("policy_violations")
    op.drop_table("governance_overrides")
    op.drop_table("emergency_stops")
    op.drop_table("human_interventions")
    op.drop_table("governance_approval_requests")
    op.drop_table("governance_policies")
