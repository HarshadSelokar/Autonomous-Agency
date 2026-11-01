"""
Alembic migration 035: Create Phase 39 Resilience V2 tables.
"""

from alembic import op
import sqlalchemy as sa

revision = '035'
down_revision = '034'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. resilience_v2_policies
    op.create_table(
        'resilience_v2_policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('circuit_breaker_threshold', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('auto_self_healing', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_resilience_v2_policies_tenant_id', 'resilience_v2_policies', ['tenant_id'])

    # 2. self_healing_logs
    op.create_table(
        'self_healing_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fault_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='MODERATE'),
        sa.Column('action_taken', sa.String(length=50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('details', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_self_healing_logs_tenant_id', 'self_healing_logs', ['tenant_id'])


def downgrade() -> None:
    op.drop_index('ix_self_healing_logs_tenant_id', table_name='self_healing_logs')
    op.drop_table('self_healing_logs')

    op.drop_index('ix_resilience_v2_policies_tenant_id', table_name='resilience_v2_policies')
    op.drop_table('resilience_v2_policies')
