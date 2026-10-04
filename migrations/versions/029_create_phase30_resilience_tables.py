"""
Alembic migration 029: Create Phase 30 Resilience, Security, Audit & DR database tables.
"""

from alembic import op
import sqlalchemy as sa

revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. circuit_breakers
    op.create_table(
        'circuit_breakers',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('dependency_name', sa.String(length=255), nullable=False),
        sa.Column('state', sa.String(length=64), nullable=False, server_default='CLOSED'),
        sa.Column('failure_threshold', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('recovery_time_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_state_change_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
    )
    op.create_index('ix_circuit_breakers_dependency', 'circuit_breakers', ['dependency_name'])

    # 2. resilience_policies
    op.create_table(
        'resilience_policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('target_name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('retry_policy_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('timeout_policy_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('circuit_breaker_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fallback_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('degradation_behavior', sa.String(length=64), nullable=False, server_default='NORMAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_resilience_policies_target', 'resilience_policies', ['target_name'])

    # 3. security_incidents
    op.create_table(
        'security_incidents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('severity', sa.String(length=64), nullable=False, server_default='HIGH'),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='DETECTED'),
        sa.Column('affected_components_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_sec_incidents_severity', 'security_incidents', ['severity'])
    op.create_index('ix_sec_incidents_status', 'security_incidents', ['status'])

    # 4. security_signals
    op.create_table(
        'security_signals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('signal_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=64), nullable=False, server_default='HIGH'),
        sa.Column('raw_content', sa.Text(), nullable=False, server_default=''),
        sa.Column('sanitized_content', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sec_signals_type', 'security_signals', ['signal_type'])

    # 5. audit_trail_logs
    op.create_table(
        'audit_trail_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('actor_type', sa.String(length=64), nullable=False, server_default='AGENT'),
        sa.Column('enterprise_id', sa.String(length=64), nullable=True),
        sa.Column('company_id', sa.String(length=64), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('resource', sa.String(length=255), nullable=False),
        sa.Column('previous_state', sa.Text(), nullable=True),
        sa.Column('new_state', sa.Text(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
    )
    op.create_index('ix_audit_logs_actor', 'audit_trail_logs', ['actor_id'])
    op.create_index('ix_audit_logs_action', 'audit_trail_logs', ['action'])

    # 6. dependency_health_snapshots
    op.create_table(
        'dependency_health_snapshots',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('dependency_name', sa.String(length=255), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_rate_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('circuit_state', sa.String(length=64), nullable=False, server_default='CLOSED'),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_dep_health_name', 'dependency_health_snapshots', ['dependency_name'])

    # 7. production_readiness_items
    op.create_table(
        'production_readiness_items',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('requirement', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='PASSED'),
        sa.Column('evidence_reference', sa.Text(), nullable=False, server_default=''),
        sa.Column('tested_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_readiness_domain', 'production_readiness_items', ['domain'])


def downgrade() -> None:
    op.drop_table('production_readiness_items')
    op.drop_table('dependency_health_snapshots')
    op.drop_table('audit_trail_logs')
    op.drop_table('security_signals')
    op.drop_table('security_incidents')
    op.drop_table('resilience_policies')
    op.drop_table('circuit_breakers')
