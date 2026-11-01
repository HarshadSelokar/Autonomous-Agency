"""
Alembic migration 032: Create Phase 35 Resource Quotas, Budgets, and Cost Governance tables.
"""

from alembic import op
import sqlalchemy as sa

revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. resource_budgets
    op.create_table(
        'resource_budgets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=True),
        sa.Column('budget_type', sa.String(length=32), nullable=False, server_default='COST'),
        sa.Column('allocated_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('used_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reserved_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(length=16), nullable=False, server_default='USD'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_resource_budgets_tenant_id', 'resource_budgets', ['tenant_id'])
    op.create_index('ix_resource_budgets_project_id', 'resource_budgets', ['project_id'])
    op.create_index('ix_resource_budgets_type', 'resource_budgets', ['budget_type'])

    # 2. cost_records
    op.create_table(
        'cost_records',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.String(length=64), nullable=True),
        sa.Column('task_id', sa.String(length=64), nullable=True),
        sa.Column('agent_id', sa.String(length=64), nullable=True),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('tokens_prompt', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_completion', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_cost_records_tenant_id', 'cost_records', ['tenant_id'])
    op.create_index('ix_cost_records_project_id', 'cost_records', ['project_id'])


def downgrade() -> None:
    op.drop_index('ix_cost_records_project_id', table_name='cost_records')
    op.drop_index('ix_cost_records_tenant_id', table_name='cost_records')
    op.drop_table('cost_records')

    op.drop_index('ix_resource_budgets_type', table_name='resource_budgets')
    op.drop_index('ix_resource_budgets_project_id', table_name='resource_budgets')
    op.drop_index('ix_resource_budgets_tenant_id', table_name='resource_budgets')
    op.drop_table('resource_budgets')
