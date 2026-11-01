"""create phase16 autonomous company tables

Revision ID: 018
Revises: 017
Create Date: 2026-09-16 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. companies
    op.create_table(
        'companies',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('mission', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('settings_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_companies_code', 'companies', ['code'])

    # 2. company_operating_cycles
    op.create_table(
        'company_operating_cycles',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('cycle_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('state', sa.String(length=32), nullable=False, server_default='CREATED'),
        sa.Column('checkpoint_data_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('initiated_by_id', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_operating_cycles_company_id', 'company_operating_cycles', ['company_id'])

    # 3. company_strategies
    op.create_table(
        'company_strategies',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('themes_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('constraints_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('priorities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('targets_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('proposer_id', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('approved_by_id', sa.String(length=64), nullable=True),
        sa.Column('previous_version_id', sa.String(length=64), nullable=True),
        sa.Column('change_rationale', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_strategies_company_id', 'company_strategies', ['company_id'])

    # 4. strategic_objectives
    op.create_table(
        'strategic_objectives',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('target_metric', sa.String(length=64), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('current_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategic_objectives_company_id', 'strategic_objectives', ['company_id'])

    # 5. strategic_initiatives
    op.create_table(
        'strategic_initiatives',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('strategic_objective_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('lead_department_id', sa.String(length=64), nullable=True),
        sa.Column('project_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('budget_tokens', sa.Integer(), nullable=False, server_default='1000000'),
        sa.Column('spent_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategic_initiatives_strategic_objective_id', 'strategic_initiatives', ['strategic_objective_id'])

    # 6. company_metric_snapshots
    op.create_table(
        'company_metric_snapshots',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('metric_name', sa.String(length=64), nullable=False),
        sa.Column('value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('target_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('scope_id', sa.String(length=64), nullable=True),
        sa.Column('trend', sa.String(length=32), nullable=False, server_default='STABLE'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('freshness_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('provenance_sources_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_metric_snapshots_company_id', 'company_metric_snapshots', ['company_id'])
    op.create_index('ix_company_metric_snapshots_metric_name', 'company_metric_snapshots', ['metric_name'])

    # 7. company_health_snapshots
    op.create_table(
        'company_health_snapshots',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('operational_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('execution_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('delivery_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('quality_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('workforce_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('reliability_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('resource_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('governance_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('security_health', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('overall_status', sa.String(length=32), nullable=False, server_default='HEALTHY'),
        sa.Column('explanation', sa.Text(), nullable=False, server_default=''),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_health_snapshots_company_id', 'company_health_snapshots', ['company_id'])

    # 8. company_risks
    op.create_table(
        'company_risks',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False, server_default='OPERATIONAL'),
        sa.Column('probability', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('impact', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('affected_entity_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('mitigation_plan', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_risks_company_id', 'company_risks', ['company_id'])

    # 9. company_opportunities
    op.create_table(
        'company_opportunities',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False, server_default='EFFICIENCY'),
        sa.Column('expected_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('required_resources', sa.Text(), nullable=False, server_default=''),
        sa.Column('affected_objective_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_opportunities_company_id', 'company_opportunities', ['company_id'])

    # 10. strategic_analyses
    op.create_table(
        'strategic_analyses',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('cycle_id', sa.String(length=64), nullable=True),
        sa.Column('current_situation', sa.Text(), nullable=False, server_default=''),
        sa.Column('observed_facts_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('trends_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('opportunities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('constraints_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('potential_causes_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('alternatives_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('required_resources', sa.Text(), nullable=False, server_default=''),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('model_used', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategic_analyses_company_id', 'strategic_analyses', ['company_id'])

    # 11. strategy_proposals
    op.create_table(
        'strategy_proposals',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('proposal_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('proposal', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('benefits', sa.Text(), nullable=False, server_default=''),
        sa.Column('resource_impact', sa.Text(), nullable=False, server_default=''),
        sa.Column('risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('dependencies_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('affected_departments_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('reversibility', sa.String(length=32), nullable=False, server_default='HIGH'),
        sa.Column('governance_level', sa.String(length=64), nullable=False, server_default='MANAGER_APPROVAL'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('proposed_by_id', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategy_proposals_company_id', 'strategy_proposals', ['company_id'])

    # 12. portfolio_items
    op.create_table(
        'portfolio_items',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('item_type', sa.String(length=32), nullable=False, server_default='PROJECT'),
        sa.Column('reference_id', sa.String(length=64), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('progress_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('resource_utilization_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('has_bottleneck', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('bottleneck_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_portfolio_items_company_id', 'portfolio_items', ['company_id'])

    # 13. resource_allocation_plans
    op.create_table(
        'resource_allocation_plans',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('cycle_id', sa.String(length=64), nullable=True),
        sa.Column('demand_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('allocations_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('constraints_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('tradeoffs_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approved_by_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resource_allocation_plans_company_id', 'resource_allocation_plans', ['company_id'])

    # 14. continuous_improvement_proposals
    op.create_table(
        'continuous_improvement_proposals',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False, server_default='PROCESS'),
        sa.Column('source_event_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('proposed_change', sa.Text(), nullable=False),
        sa.Column('expected_impact', sa.Text(), nullable=False, server_default=''),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_continuous_improvement_proposals_company_id', 'continuous_improvement_proposals', ['company_id'])

    # 15. strategy_simulations
    op.create_table(
        'strategy_simulations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('input_parameters_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('projected_outcomes_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('resource_effects_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('projected_risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('is_authoritative', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategy_simulations_company_id', 'strategy_simulations', ['company_id'])


def downgrade() -> None:
    op.drop_table('strategy_simulations')
    op.drop_table('continuous_improvement_proposals')
    op.drop_table('resource_allocation_plans')
    op.drop_table('portfolio_items')
    op.drop_table('strategy_proposals')
    op.drop_table('strategic_analyses')
    op.drop_table('company_opportunities')
    op.drop_table('company_risks')
    op.drop_table('company_health_snapshots')
    op.drop_table('company_metric_snapshots')
    op.drop_table('strategic_initiatives')
    op.drop_table('strategic_objectives')
    op.drop_table('company_strategies')
    op.drop_table('company_operating_cycles')
    op.drop_table('companies')
