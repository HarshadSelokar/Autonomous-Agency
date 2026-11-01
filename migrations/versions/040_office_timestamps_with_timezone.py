"""
Alembic migration 040: store Pixel Office timestamps with a time zone.

The application writes timezone-aware datetimes; PostgreSQL rejects those for
TIMESTAMP WITHOUT TIME ZONE columns. Existing values are taken to be UTC.
"""

from alembic import op
import sqlalchemy as sa

revision = '040'
down_revision = '039'
branch_labels = None
depends_on = None

COLUMNS = [
    ('office_workstations', 'updated_at'),
    ('office_activity_feed', 'created_at'),
    ('human_attention_queue', 'created_at'),
]


def upgrade() -> None:
    is_postgres = op.get_bind().dialect.name == 'postgresql'
    for table, column in COLUMNS:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                column,
                type_=sa.DateTime(timezone=True),
                existing_type=sa.DateTime(),
                existing_nullable=False,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'" if is_postgres else None,
            )


def downgrade() -> None:
    is_postgres = op.get_bind().dialect.name == 'postgresql'
    for table, column in COLUMNS:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                column,
                type_=sa.DateTime(),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=False,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'" if is_postgres else None,
            )
