"""Create Phase 22 Multi-Agent Swarm & Distributed Execution Tables

Revision ID: 021
Revises: 020
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. swarms
    op.create_table(
        'swarms',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('parent_task_id', sa.String(length=36), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('manager_id', sa.String(length=36), nullable=False),
        sa.Column('objective_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('coordinator_member_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CREATED'),
        sa.Column('coordination_mode', sa.String(length=50), nullable=False, server_default='PARALLEL'),
        sa.Column('depth', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('governance_context', JSON(), nullable=True),
        sa.Column('concurrency_limit', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_agents', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. swarm_members
    op.create_table(
        'swarm_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('swarm_id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=36), nullable=False),
        sa.Column('agent_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('capability', sa.String(length=100), nullable=False),
        sa.Column('assigned_task_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='INVITED'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_stats', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['swarm_id'], ['swarms.id'], ondelete='CASCADE')
    )

    # 3. swarm_budgets
    op.create_table(
        'swarm_budgets',
        sa.Column('swarm_id', sa.String(length=36), nullable=False),
        sa.Column('max_execution_time_seconds', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('max_model_cost', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('max_tool_calls', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='500000'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_swarm_depth', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('current_execution_time_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_model_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('current_tool_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_retries', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('swarm_id'),
        sa.ForeignKeyConstraint(['swarm_id'], ['swarms.id'], ondelete='CASCADE')
    )

    # 4. swarm_results
    op.create_table(
        'swarm_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('swarm_id', sa.String(length=36), nullable=False),
        sa.Column('parent_task_id', sa.String(length=36), nullable=False),
        sa.Column('member_results', JSON(), nullable=True),
        sa.Column('subtask_status', JSON(), nullable=True),
        sa.Column('artifacts', JSON(), nullable=True),
        sa.Column('evidence_ids', JSON(), nullable=True),
        sa.Column('disagreements', JSON(), nullable=True),
        sa.Column('unresolved_issues', JSON(), nullable=True),
        sa.Column('aggregated_result', JSON(), nullable=True),
        sa.Column('aggregation_strategy', sa.String(length=100), nullable=False, server_default='DETERMINISTIC_MERGE'),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['swarm_id'], ['swarms.id'], ondelete='CASCADE')
    )

    # 5. swarm_messages
    op.create_table(
        'swarm_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('swarm_id', sa.String(length=36), nullable=False),
        sa.Column('sender_id', sa.String(length=36), nullable=False),
        sa.Column('recipient_id', sa.String(length=36), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('payload', JSON(), nullable=True),
        sa.Column('correlation_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['swarm_id'], ['swarms.id'], ondelete='CASCADE')
    )

    # 6. swarm_conflicts
    op.create_table(
        'swarm_conflicts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('swarm_id', sa.String(length=36), nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('agent_a_id', sa.String(length=36), nullable=False),
        sa.Column('result_a', JSON(), nullable=True),
        sa.Column('agent_b_id', sa.String(length=36), nullable=False),
        sa.Column('result_b', JSON(), nullable=True),
        sa.Column('conflict_type', sa.String(length=100), nullable=False),
        sa.Column('resolution_strategy', sa.String(length=100), nullable=False, server_default='INDEPENDENT_VERIFICATION'),
        sa.Column('resolved_result', JSON(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['swarm_id'], ['swarms.id'], ondelete='CASCADE')
    )


def downgrade() -> None:
    op.drop_table('swarm_conflicts')
    op.drop_table('swarm_messages')
    op.drop_table('swarm_results')
    op.drop_table('swarm_budgets')
    op.drop_table('swarm_members')
    op.drop_table('swarms')
