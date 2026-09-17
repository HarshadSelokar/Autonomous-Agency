"""
Alembic migration 028: Create Phase 29 Enterprise OS database tables.
"""

from alembic import op
import sqlalchemy as sa

revision = '028_create_phase29_enterprise_tables'
down_revision = '027_create_phase28_venture_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. enterprises
    op.create_table(
        'enterprises',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='PROPOSED'),
        sa.Column('profile_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_enterprises_status', 'enterprises', ['status'])

    # 2. enterprise_topology_nodes
    op.create_table(
        'enterprise_topology_nodes',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('node_type', sa.String(length=64), nullable=False),
        sa.Column('reference_id', sa.String(length=64), nullable=True),
        sa.Column('parent_node_id', sa.String(length=64), sa.ForeignKey('enterprise_topology_nodes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('region', sa.String(length=64), nullable=False, server_default='GLOBAL'),
        sa.Column('data_classification', sa.String(length=64), nullable=False, server_default='INTERNAL'),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ent_nodes_ent_id', 'enterprise_topology_nodes', ['enterprise_id'])
    op.create_index('ix_ent_nodes_type', 'enterprise_topology_nodes', ['node_type'])

    # 3. enterprise_relationships
    op.create_table(
        'enterprise_relationships',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_node_id', sa.String(length=64), sa.ForeignKey('enterprise_topology_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_node_id', sa.String(length=64), sa.ForeignKey('enterprise_topology_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 4. enterprise_services
    op.create_table(
        'enterprise_services',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_node_id', sa.String(length=64), sa.ForeignKey('enterprise_topology_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('service_type', sa.String(length=64), nullable=False),
        sa.Column('capacity_units', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('available_units', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('sla_description', sa.Text(), nullable=False, server_default=''),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. enterprise_service_agreements
    op.create_table(
        'enterprise_service_agreements',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('service_id', sa.String(length=64), sa.ForeignKey('enterprise_services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('consumer_node_id', sa.String(length=64), sa.ForeignKey('enterprise_topology_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('allocated_units', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('cost_allocation_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 6. enterprise_portfolios & items
    op.create_table(
        'enterprise_portfolios',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('total_budget_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'enterprise_portfolio_items',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('portfolio_id', sa.String(length=64), sa.ForeignKey('enterprise_portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('reference_id', sa.String(length=64), nullable=False),
        sa.Column('priority', sa.String(length=64), nullable=False, server_default='MEDIUM'),
        sa.Column('allocated_budget_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expected_roi', sa.Float(), nullable=False, server_default='0.20'),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 7. enterprise_objectives & cascades
    op.create_table(
        'enterprise_objectives',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('target_metric', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('target_value', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('current_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('scope', sa.String(length=64), nullable=False, server_default='ENTERPRISE'),
        sa.Column('owner_node_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'objective_cascades',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('parent_objective_id', sa.String(length=64), sa.ForeignKey('enterprise_objectives.id', ondelete='CASCADE'), nullable=False),
        sa.Column('child_objective_id', sa.String(length=64), sa.ForeignKey('enterprise_objectives.id', ondelete='CASCADE'), nullable=False),
        sa.Column('child_node_id', sa.String(length=64), nullable=False),
        sa.Column('contribution_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('alignment_status', sa.String(length=64), nullable=False, server_default='ALIGNED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. enterprise_policy_profiles
    op.create_table(
        'enterprise_policy_profiles',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.String(length=64), nullable=False),
        sa.Column('mandatory_security_level', sa.String(length=64), nullable=False, server_default='HIGH'),
        sa.Column('max_single_budget_spend_usd', sa.Float(), nullable=False, server_default='50000.0'),
        sa.Column('prohibited_external_actions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('require_human_governance', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 9. enterprise_authority_grants
    op.create_table(
        'enterprise_authority_grants',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grantor_node_id', sa.String(length=64), nullable=False),
        sa.Column('grantee_node_id', sa.String(length=64), nullable=False),
        sa.Column('scope', sa.String(length=128), nullable=False),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('max_impact_usd', sa.Float(), nullable=False, server_default='100000.0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 10. enterprise_resource_pools & allocations
    op.create_table(
        'enterprise_resource_pools',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('total_capacity', sa.Float(), nullable=False, server_default='1000.0'),
        sa.Column('available_capacity', sa.Float(), nullable=False, server_default='1000.0'),
        sa.Column('unit', sa.String(length=32), nullable=False, server_default='UNITS'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'enterprise_resource_allocations',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('pool_id', sa.String(length=64), sa.ForeignKey('enterprise_resource_pools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('consumer_node_id', sa.String(length=64), nullable=False),
        sa.Column('allocated_amount', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='ALLOCATED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. enterprise_intercompany_requests
    op.create_table(
        'enterprise_intercompany_requests',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_company_id', sa.String(length=64), nullable=False),
        sa.Column('destination_company_id', sa.String(length=64), nullable=False),
        sa.Column('requester_id', sa.String(length=64), nullable=False),
        sa.Column('requested_capability', sa.String(length=255), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='PENDING'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('result_data_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 12. enterprise_risks & opportunities
    op.create_table(
        'enterprise_risks',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('impact_usd', sa.Float(), nullable=False, server_default='500000.0'),
        sa.Column('probability', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('owner_node_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'enterprise_opportunities',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('potential_value_usd', sa.Float(), nullable=False, server_default='2000000.0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.80'),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='IDENTIFIED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('enterprise_opportunities')
    op.drop_table('enterprise_risks')
    op.drop_table('enterprise_intercompany_requests')
    op.drop_table('enterprise_resource_allocations')
    op.drop_table('enterprise_resource_pools')
    op.drop_table('enterprise_authority_grants')
    op.drop_table('enterprise_policy_profiles')
    op.drop_table('objective_cascades')
    op.drop_table('enterprise_objectives')
    op.drop_table('enterprise_portfolio_items')
    op.drop_table('enterprise_portfolios')
    op.drop_table('enterprise_service_agreements')
    op.drop_table('enterprise_services')
    op.drop_table('enterprise_relationships')
    op.drop_table('enterprise_topology_nodes')
    op.drop_table('enterprises')
