"""create phase25 multi company and simulation tables

Revision ID: 024
Revises: 023
Create Date: 2026-09-17 03:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '024'
down_revision: Union[str, None] = '023'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. company_tenants
    op.create_table(
        'company_tenants',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('legal_name', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('company_type', sa.String(length=32), nullable=False, server_default='AUTONOMOUS'),
        sa.Column('industry', sa.String(length=64), nullable=False, server_default='TECHNOLOGY'),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC'),
        sa.Column('locale', sa.String(length=32), nullable=False, server_default='en_US'),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='USD'),
        sa.Column('lifecycle', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('owner_id', sa.String(length=64), nullable=False, server_default='SYSTEM'),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_tenants_slug', 'company_tenants', ['slug'], unique=False)

    # 2. company_profiles
    op.create_table(
        'company_profiles',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('operating_hours', sa.String(length=64), nullable=False, server_default='24/7'),
        sa.Column('model_routing_policy_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('tool_policy_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('governance_defaults_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('workforce_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_profiles_company_id', 'company_profiles', ['company_id'], unique=False)

    # 3. company_memberships
    op.create_table(
        'company_memberships',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='VIEWER'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_memberships_company_id', 'company_memberships', ['company_id'], unique=False)
    op.create_index('ix_company_memberships_user_id', 'company_memberships', ['user_id'], unique=False)

    # 4. company_templates
    op.create_table(
        'company_templates',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('industry', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('structure_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('default_departments_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('default_roles_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. company_relationships
    op.create_table(
        'company_relationships',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_a_id', sa.String(length=64), nullable=False),
        sa.Column('company_b_id', sa.String(length=64), nullable=False),
        sa.Column('relationship_type', sa.String(length=32), nullable=False, server_default='PARTNER'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_relationships_company_a_id', 'company_relationships', ['company_a_id'], unique=False)
    op.create_index('ix_company_relationships_company_b_id', 'company_relationships', ['company_b_id'], unique=False)

    # 6. company_data_share_requests
    op.create_table(
        'company_data_share_requests',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('source_company_id', sa.String(length=64), nullable=False),
        sa.Column('target_company_id', sa.String(length=64), nullable=False),
        sa.Column('data_scope', sa.String(length=32), nullable=False, server_default='READ_ONLY'),
        sa.Column('purpose', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='REQUESTED'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_data_share_requests_source', 'company_data_share_requests', ['source_company_id'], unique=False)
    op.create_index('ix_company_data_share_requests_target', 'company_data_share_requests', ['target_company_id'], unique=False)

    # 7. company_resource_quotas
    op.create_table(
        'company_resource_quotas',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('max_concurrent_tasks', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_concurrent_agents', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('max_monthly_model_calls', sa.Integer(), nullable=False, server_default='100000'),
        sa.Column('max_storage_mb', sa.Integer(), nullable=False, server_default='50000'),
        sa.Column('max_simulations', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_resource_quotas_company_id', 'company_resource_quotas', ['company_id'], unique=False)

    # 8. company_resource_usages
    op.create_table(
        'company_resource_usages',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('active_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_agents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_model_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('storage_mb', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_simulations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_resource_usages_company_id', 'company_resource_usages', ['company_id'], unique=False)

    # 9. company_simulations
    op.create_table(
        'company_simulations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('scenario_id', sa.String(length=64), nullable=False),
        sa.Column('snapshot_id', sa.String(length=64), nullable=False),
        sa.Column('environment', sa.String(length=32), nullable=False, server_default='SIMULATION'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('owner_id', sa.String(length=64), nullable=False, server_default='SYSTEM'),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_simulations_company_id', 'company_simulations', ['company_id'], unique=False)

    # 10. simulation_snapshots
    op.create_table(
        'simulation_snapshots',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('snapshot_name', sa.String(length=128), nullable=False),
        sa.Column('snapshot_data_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_simulation_snapshots_company_id', 'simulation_snapshots', ['company_id'], unique=False)

    # 11. simulation_scenarios
    op.create_table(
        'simulation_scenarios',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('variables_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_simulation_scenarios_company_id', 'simulation_scenarios', ['company_id'], unique=False)

    # 12. simulation_results
    op.create_table(
        'simulation_results',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('simulation_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('scenario_name', sa.String(length=128), nullable=False),
        sa.Column('baseline_metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('simulated_metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('variance_analysis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.90'),
        sa.Column('produced_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_simulation_results_simulation_id', 'simulation_results', ['simulation_id'], unique=False)
    op.create_index('ix_simulation_results_company_id', 'simulation_results', ['company_id'], unique=False)

    # 13. simulation_financial_records
    op.create_table(
        'simulation_financial_records',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('simulation_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('record_type', sa.String(length=64), nullable=False, server_default='SIMULATED_REVENUE'),
        sa.Column('amount_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='USD'),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sim_fin_records_simulation_id', 'simulation_financial_records', ['simulation_id'], unique=False)
    op.create_index('ix_sim_fin_records_company_id', 'simulation_financial_records', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_table('simulation_financial_records')
    op.drop_table('simulation_results')
    op.drop_table('simulation_scenarios')
    op.drop_table('simulation_snapshots')
    op.drop_table('company_simulations')
    op.drop_table('company_resource_usages')
    op.drop_table('company_resource_quotas')
    op.drop_table('company_data_share_requests')
    op.drop_table('company_relationships')
    op.drop_table('company_templates')
    op.drop_table('company_memberships')
    op.drop_table('company_profiles')
    op.drop_table('company_tenants')
