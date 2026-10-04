"""
Alembic migration 037: Software Studio tables (dev projects, tickets, activity feed)
and password credentials on users.
"""

from alembic import op
import sqlalchemy as sa

revision = '037'
down_revision = '036'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=256), nullable=True))

    op.create_table(
        'dev_projects',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=True),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='CREATED'),
        sa.Column('repo_url', sa.String(length=1024), nullable=True),
        sa.Column('local_path', sa.String(length=1024), nullable=True),
        sa.Column('workspace_path', sa.String(length=1024), nullable=False, server_default=''),
        sa.Column('branch', sa.String(length=256), nullable=False, server_default=''),
        sa.Column('base_commit', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('test_command', sa.String(length=512), nullable=True),
        sa.Column('provider', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('model', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('usage', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_dev_projects_tenant_id', 'dev_projects', ['tenant_id'])
    op.create_index('ix_dev_projects_status', 'dev_projects', ['status'])

    op.create_table(
        'dev_tickets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.String(length=64), sa.ForeignKey('dev_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('acceptance_criteria', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='TODO'),
        sa.Column('depends_on', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('assignee_id', sa.String(length=128), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('feedback', sa.Text(), nullable=False, server_default=''),
        sa.Column('commit_sha', sa.String(length=64), nullable=True),
        sa.Column('result_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_dev_tickets_project_id', 'dev_tickets', ['project_id'])
    op.create_index('ix_dev_tickets_status', 'dev_tickets', ['status'])

    op.create_table(
        'dev_activity_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.String(length=64), sa.ForeignKey('dev_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.String(length=64), nullable=True),
        sa.Column('actor_id', sa.String(length=128), nullable=False),
        sa.Column('actor_name', sa.String(length=128), nullable=False),
        sa.Column('actor_role', sa.String(length=32), nullable=False),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('summary', sa.String(length=512), nullable=False),
        sa.Column('detail', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('project_id', 'sequence', name='uq_dev_activity_project_seq'),
    )
    op.create_index('ix_dev_activity_events_project_id', 'dev_activity_events', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_dev_activity_events_project_id', table_name='dev_activity_events')
    op.drop_table('dev_activity_events')
    op.drop_index('ix_dev_tickets_status', table_name='dev_tickets')
    op.drop_index('ix_dev_tickets_project_id', table_name='dev_tickets')
    op.drop_table('dev_tickets')
    op.drop_index('ix_dev_projects_status', table_name='dev_projects')
    op.drop_index('ix_dev_projects_tenant_id', table_name='dev_projects')
    op.drop_table('dev_projects')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('password_hash')
