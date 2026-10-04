"""
Alembic migration 039: tenant_id on every table, and studio team / approval columns.

Tenant scoping is enforced in the ORM for every model (see
src/infrastructure/tenant_context.py), so every table needs the column. Existing rows keep
tenant_id NULL: they stay visible to platform admins and are hidden from tenant users.
"""

from alembic import op
import sqlalchemy as sa

revision = '039'
down_revision = '038'
branch_labels = None
depends_on = None

SKIPPED_TABLES = {'alembic_version'}


def _tables_without_tenant_id() -> list[str]:
    inspector = sa.inspect(op.get_bind())
    return [
        table
        for table in sorted(inspector.get_table_names())
        if table not in SKIPPED_TABLES
        and 'tenant_id' not in {column['name'] for column in inspector.get_columns(table)}
    ]


def upgrade() -> None:
    added = _tables_without_tenant_id()
    for table in added:
        op.add_column(table, sa.Column('tenant_id', sa.String(length=64), nullable=True))
        op.create_index(f'ix_{table}_tenant_id', table, ['tenant_id'])
    # Recorded so downgrade removes exactly what this migration added
    op.create_table(
        'tenant_scope_migration_log',
        sa.Column('table_name', sa.String(length=128), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=True),
    )
    log = sa.table('tenant_scope_migration_log', sa.column('table_name', sa.String))
    if added:
        op.bulk_insert(log, [{'table_name': table} for table in added])

    # A tenant row belongs to itself, so its own users can read it
    op.execute("UPDATE tenants SET tenant_id = id WHERE tenant_id IS NULL")

    with op.batch_alter_table('dev_projects') as batch_op:
        batch_op.add_column(sa.Column('members', sa.JSON(), nullable=False, server_default='[]'))
        batch_op.add_column(
            sa.Column('require_approval', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    with op.batch_alter_table('dev_tickets') as batch_op:
        batch_op.add_column(sa.Column('approval', sa.String(length=16), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('approval_feedback', sa.Text(), nullable=False, server_default=''))


def downgrade() -> None:
    with op.batch_alter_table('dev_tickets') as batch_op:
        batch_op.drop_column('approval_feedback')
        batch_op.drop_column('approval')
    with op.batch_alter_table('dev_projects') as batch_op:
        batch_op.drop_column('require_approval')
        batch_op.drop_column('members')

    rows = op.get_bind().execute(sa.text("SELECT table_name FROM tenant_scope_migration_log")).fetchall()
    op.drop_table('tenant_scope_migration_log')
    for (table,) in rows:
        op.drop_index(f'ix_{table}_tenant_id', table_name=table)
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column('tenant_id')
