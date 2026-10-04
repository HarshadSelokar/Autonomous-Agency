"""
Alembic migration 034: Create Phase 38 Event-Driven Operations outbox updates.
"""

from alembic import op
import sqlalchemy as sa

revision = '034'
down_revision = '033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure tenant_id column exists on outbox_messages table
    with op.batch_alter_table('outbox_messages') as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(length=64), nullable=True))
        batch_op.create_index('ix_outbox_messages_tenant_id', ['tenant_id'])


def downgrade() -> None:
    with op.batch_alter_table('outbox_messages') as batch_op:
        batch_op.drop_index('ix_outbox_messages_tenant_id')
        batch_op.drop_column('tenant_id')
