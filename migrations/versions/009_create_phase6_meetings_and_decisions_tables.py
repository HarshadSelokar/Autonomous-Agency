"""Create Phase 6 meetings, participants, attendance, agenda, decisions, and decision_audits tables

Revision ID: 009_create_phase6_meetings_and_decisions_tables
Revises: 008_create_phase5_communication_tables
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_create_phase6_meetings_and_decisions_tables"
down_revision: str | None = "008_create_phase5_communication_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Meetings table
    op.create_table(
        "meetings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("organizer_employee_id", sa.String(length=64), nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("objective_id", sa.String(length=64), nullable=True),
        sa.Column("plan_id", sa.String(length=64), nullable=True),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["organizer_employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_meetings_status", "meetings", ["status"])
    op.create_index("ix_meetings_organizer", "meetings", ["organizer_employee_id"])
    op.create_index("ix_meetings_objective", "meetings", ["objective_id"])
    op.create_index("ix_meetings_task", "meetings", ["task_id"])

    # 2. Meeting Participants table
    op.create_table(
        "meeting_participants",
        sa.Column("meeting_id", sa.String(length=64), nullable=False),
        sa.Column("employee_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("meeting_id", "employee_id"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_meeting_participants_employee", "meeting_participants", ["employee_id"])

    # 3. Meeting Attendance table
    op.create_table(
        "meeting_attendance",
        sa.Column("meeting_id", sa.String(length=64), nullable=False),
        sa.Column("employee_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint("meeting_id", "employee_id"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_meeting_attendance_employee", "meeting_attendance", ["employee_id"])

    # 4. Meeting Agenda Items table
    op.create_table(
        "meeting_agenda_items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("meeting_id", sa.String(length=64), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.String(length=2048), nullable=True),
        sa.Column("owner_employee_id", sa.String(length=64), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("objective_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_employee_id"], ["employees.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_meeting_agenda_items_meeting", "meeting_agenda_items", ["meeting_id"])

    # 5. Organizational Decisions table
    op.create_table(
        "decisions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("question", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("decision_maker_employee_id", sa.String(length=64), nullable=False),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("approving_authority_role", sa.String(length=64), nullable=True),
        sa.Column("chosen_option", sa.String(length=512), nullable=True),
        sa.Column("alternatives", sa.JSON(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("consequences", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("meeting_id", sa.String(length=64), nullable=True),
        sa.Column("objective_id", sa.String(length=64), nullable=True),
        sa.Column("plan_id", sa.String(length=64), nullable=True),
        sa.Column("task_id", sa.String(length=64), nullable=True),
        sa.Column("previous_decision_id", sa.String(length=64), nullable=True),
        sa.Column("provenance", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["decision_maker_employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["previous_decision_id"], ["decisions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_decisions_status", "decisions", ["status"])
    op.create_index("ix_decisions_maker", "decisions", ["decision_maker_employee_id"])
    op.create_index("ix_decisions_meeting", "decisions", ["meeting_id"])
    op.create_index("ix_decisions_objective", "decisions", ["objective_id"])
    op.create_index("ix_decisions_task", "decisions", ["task_id"])

    # 6. Decision Audits table
    op.create_table(
        "decision_audits",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=False),
        sa.Column("actor_employee_id", sa.String(length=64), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=False),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_employee_id"], ["employees.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_decision_audits_decision", "decision_audits", ["decision_id"])


def downgrade() -> None:
    op.drop_table("decision_audits")
    op.drop_table("decisions")
    op.drop_table("meeting_agenda_items")
    op.drop_table("meeting_attendance")
    op.drop_table("meeting_participants")
    op.drop_table("meetings")
