"""
Alembic migration 033: Create Phase 37 Workflow Engine 2.0 tables.
"""

from alembic import op
import sqlalchemy as sa

revision = '033'
down_revision = '032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. workflow_definitions
    op.create_table(
        'workflow_definitions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('nodes', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_workflow_definitions_tenant_id', 'workflow_definitions', ['tenant_id'])

    # 2. workflow_instances
    op.create_table(
        'workflow_instances',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('definition_id', sa.String(length=64), sa.ForeignKey('workflow_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='RUNNING'),
        sa.Column('current_node_id', sa.String(length=64), nullable=True),
        sa.Column('completed_nodes', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('execution_context', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_workflow_instances_tenant_id', 'workflow_instances', ['tenant_id'])
    op.create_index('ix_workflow_instances_definition_id', 'workflow_instances', ['definition_id'])
    op.create_index('ix_workflow_instances_status', 'workflow_instances', ['status'])


def downgrade() -> None:
    op.drop_index('ix_workflow_instances_status', table_name='workflow_instances')
    op.drop_index('ix_workflow_instances_definition_id', table_name='workflow_instances')
    op.drop_index('ix_workflow_instances_tenant_id', table_name='workflow_instances')
    op.drop_table('workflow_instances')

    op.drop_index('ix_workflow_definitions_tenant_id', table_name='workflow_definitions')
    op.drop_table('workflow_definitions')
