"""
Alembic migration 036: Create Phase 40 Audit 2.0 tables.
"""

from alembic import op
import sqlalchemy as sa

revision = '036'
down_revision = '035'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_records_v2',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('resource', sa.String(length=256), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('prev_hash', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_records_v2_tenant_id', 'audit_records_v2', ['tenant_id'])
    op.create_index('ix_audit_records_v2_actor_id', 'audit_records_v2', ['actor_id'])
    op.create_index('ix_audit_records_v2_action_type', 'audit_records_v2', ['action_type'])


def downgrade() -> None:
    op.drop_index('ix_audit_records_v2_action_type', table_name='audit_records_v2')
    op.drop_index('ix_audit_records_v2_actor_id', table_name='audit_records_v2')
    op.drop_index('ix_audit_records_v2_tenant_id', table_name='audit_records_v2')
    op.drop_table('audit_records_v2')
