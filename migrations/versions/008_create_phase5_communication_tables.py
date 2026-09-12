"""Create Phase 5 conversations, messages, and outbox_messages tables

Revision ID: 008_create_phase5_communication_tables
Revises: 007_create_phase4_task_engine_tables
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_create_phase5_communication_tables"
down_revision: str | None = "007_create_phase4_task_engine_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("conversation_type", sa.String(length=50), nullable=False),
        sa.Column("created_by_employee_id", sa.String(length=36), nullable=False),
        sa.Column("participants_json", sa.Text(), nullable=False),
        sa.Column("related_objective_id", sa.String(length=36), nullable=True),
        sa.Column("related_plan_id", sa.String(length=36), nullable=True),
        sa.Column("related_task_id", sa.String(length=36), nullable=True),
        sa.Column("related_project_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_type", "conversations", ["conversation_type"])
    op.create_index("ix_conversations_created_by", "conversations", ["created_by_employee_id"])
    op.create_index("ix_conversations_task", "conversations", ["related_task_id"])
    op.create_index("ix_conversations_objective", "conversations", ["related_objective_id"])

    # 2. Messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("sender_employee_id", sa.String(length=36), nullable=False),
        sa.Column("sender_agent_id", sa.String(length=36), nullable=True),
        sa.Column("sender_run_id", sa.String(length=36), nullable=True),
        sa.Column("message_type", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("references_json", sa.Text(), nullable=False),
        sa.Column("reply_to_message_id", sa.String(length=36), nullable=True),
        sa.Column("correlation_id", sa.String(length=36), nullable=False),
        sa.Column("delivery_state", sa.String(length=50), nullable=False, server_default="CREATED"),
        sa.Column("acknowledgements_json", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_employee_id", "messages", ["sender_employee_id"])
    op.create_index("ix_messages_type", "messages", ["message_type"])
    op.create_index("ix_messages_delivery_state", "messages", ["delivery_state"])
    op.create_index("ix_messages_reply_to", "messages", ["reply_to_message_id"])

    # 3. Outbox Messages table
    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_messages_status", "outbox_messages", ["status"])
    op.create_index("ix_outbox_messages_event_type", "outbox_messages", ["event_type"])


def downgrade() -> None:
    op.drop_table("outbox_messages")
    op.drop_table("messages")
    op.drop_table("conversations")
