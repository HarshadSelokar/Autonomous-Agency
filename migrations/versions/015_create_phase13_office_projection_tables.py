"""Create Phase 13 Pixel Office projection tables

Revision ID: 015_create_phase13_office_projection_tables
Revises: 014_create_phase11_12_governance_and_model_routing_tables
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Office Workstations
    op.create_table(
        "office_workstations",
        sa.Column("employee_id", sa.String(length=64), nullable=False),
        sa.Column("employee_name", sa.String(length=128), nullable=False),
        sa.Column("employee_title", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("department_id", sa.String(length=64), nullable=True),
        sa.Column("manager_id", sa.String(length=64), nullable=True),
        sa.Column("desk_id", sa.String(length=64), nullable=False),
        sa.Column("area_type", sa.String(length=64), nullable=False),
        sa.Column("visual_state", sa.String(length=64), nullable=False),
        sa.Column("current_task_id", sa.String(length=64), nullable=True),
        sa.Column("current_task_title", sa.String(length=256), nullable=True),
        sa.Column("current_project_id", sa.String(length=64), nullable=True),
        sa.Column("current_project_name", sa.String(length=128), nullable=True),
        sa.Column("current_activity_summary", sa.Text(), nullable=False),
        sa.Column("active_agent_id", sa.String(length=64), nullable=True),
        sa.Column("active_tool_name", sa.String(length=128), nullable=True),
        sa.Column("active_model_id", sa.String(length=128), nullable=True),
        sa.Column("is_manager", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("employee_id"),
    )
    op.create_index("ix_office_workstations_employee_id", "office_workstations", ["employee_id"])
    op.create_index("ix_office_workstations_department_id", "office_workstations", ["department_id"])
    op.create_index("ix_office_workstations_visual_state", "office_workstations", ["visual_state"])

    # 2. Office Activity Feed
    op.create_table(
        "office_activity_feed",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_office_activity_feed_id", "office_activity_feed", ["id"])
    op.create_index("ix_office_activity_feed_category", "office_activity_feed", ["category"])
    op.create_index("ix_office_activity_feed_created_at", "office_activity_feed", ["created_at"])

    # 3. Human Attention Queue
    op.create_table(
        "human_attention_queue",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("attention_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("action_url", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_human_attention_queue_id", "human_attention_queue", ["id"])
    op.create_index("ix_human_attention_queue_attention_type", "human_attention_queue", ["attention_type"])


def downgrade() -> None:
    op.drop_table("human_attention_queue")
    op.drop_table("office_activity_feed")
    op.drop_table("office_workstations")
