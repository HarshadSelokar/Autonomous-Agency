"""Create agent_checkpoints table

Revision ID: 004_create_agent_checkpoints
Revises: 003_create_agent_run_steps
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_checkpoints",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("current_state", sa.String(length=32), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("context_reference", sa.JSON(), nullable=False),
        sa.Column("output_so_far", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_checkpoints_run_id"), "agent_checkpoints", ["run_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_checkpoints_run_id"), table_name="agent_checkpoints")
    op.drop_table("agent_checkpoints")
