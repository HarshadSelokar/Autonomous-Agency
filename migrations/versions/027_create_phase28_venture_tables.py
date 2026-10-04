"""create phase28 venture and innovation tables

Revision ID: 027
Revises: 026
Create Date: 2026-09-17 15:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '027'
down_revision: Union[str, None] = '026'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. innovation_opportunities
    op.create_table(
        'innovation_opportunities',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=64), nullable=False, server_default='RESEARCH_SIGNAL'),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('customer_need', sa.Text(), nullable=False),
        sa.Column('market_signal_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('evidence_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('strategic_relevance', sa.Float(), nullable=False, server_default='0.80'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.50'),
        sa.Column('assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('potential_impact', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DISCOVERED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_innovation_opportunities_company_id', 'innovation_opportunities', ['company_id'], unique=False)

    # 2. innovation_ideas
    op.create_table(
        'innovation_ideas',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('opportunity_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('proposed_solution', sa.Text(), nullable=False),
        sa.Column('target_customer', sa.Text(), nullable=False),
        sa.Column('value_proposition', sa.Text(), nullable=False),
        sa.Column('differentiator', sa.Text(), nullable=False),
        sa.Column('assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('dependencies_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('required_capabilities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_innovation_ideas_company_id', 'innovation_ideas', ['company_id'], unique=False)
    op.create_index('ix_innovation_ideas_opportunity_id', 'innovation_ideas', ['opportunity_id'], unique=False)

    # 3. business_hypotheses
    op.create_table(
        'business_hypotheses',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('idea_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('assumption', sa.Text(), nullable=False),
        sa.Column('supporting_evidence_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.50'),
        sa.Column('validation_method', sa.String(length=64), nullable=False, server_default='RESEARCH_AND_SIMULATION'),
        sa.Column('failure_condition', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_hypotheses_company_id', 'business_hypotheses', ['company_id'], unique=False)
    op.create_index('ix_business_hypotheses_idea_id', 'business_hypotheses', ['idea_id'], unique=False)

    # 4. product_concepts
    op.create_table(
        'product_concepts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('idea_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('target_segment', sa.Text(), nullable=False),
        sa.Column('capabilities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('value_proposition', sa.Text(), nullable=False),
        sa.Column('pricing_hypothesis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('distribution_channel', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_product_concepts_company_id', 'product_concepts', ['company_id'], unique=False)

    # 5. business_model_concepts
    op.create_table(
        'business_model_concepts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('idea_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('revenue_model', sa.String(length=64), nullable=False, server_default='SUBSCRIPTION'),
        sa.Column('pricing_model_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('acquisition_strategy', sa.Text(), nullable=False),
        sa.Column('cost_structure_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('gross_margin_est', sa.Float(), nullable=False, server_default='0.70'),
        sa.Column('operating_model', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_model_concepts_company_id', 'business_model_concepts', ['company_id'], unique=False)

    # 6. venture_business_cases
    op.create_table(
        'venture_business_cases',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('opportunity_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('market_assumptions_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('financial_model_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('workforce_reqs_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('infra_reqs_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('risk_analysis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('scenarios_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('expected_roi', sa.Float(), nullable=False, server_default='0.35'),
        sa.Column('uncertainty_score', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_business_cases_company_id', 'venture_business_cases', ['company_id'], unique=False)

    # 7. venture_validations
    op.create_table(
        'venture_validations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('opportunity_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('validation_method', sa.String(length=64), nullable=False),
        sa.Column('evidence_summary', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('unresolved_assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_validations_company_id', 'venture_validations', ['company_id'], unique=False)

    # 8. venture_experiments
    op.create_table(
        'venture_experiments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('control_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('treatment_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('duration_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('success_criteria_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_experiments_company_id', 'venture_experiments', ['company_id'], unique=False)

    # 9. innovation_reviews
    op.create_table(
        'innovation_reviews',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('strategic_fit_score', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('customer_value_score', sa.Float(), nullable=False, server_default='0.90'),
        sa.Column('technical_feasibility_score', sa.Float(), nullable=False, server_default='0.80'),
        sa.Column('economic_viability_score', sa.Float(), nullable=False, server_default='0.75'),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.30'),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.82'),
        sa.Column('recommendation', sa.String(length=64), nullable=False, server_default='PROCEED_TO_GOVERNANCE'),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_innovation_reviews_company_id', 'innovation_reviews', ['company_id'], unique=False)

    # 10. venture_proposals
    op.create_table(
        'venture_proposals',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('opportunity_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('venture_type', sa.String(length=32), nullable=False, server_default='NEW_COMPANY'),
        sa.Column('business_case_id', sa.String(length=64), nullable=False),
        sa.Column('required_budget_usd', sa.Integer(), nullable=False, server_default='15000000'),
        sa.Column('required_workforce_count', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('risk_level', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_proposals_company_id', 'venture_proposals', ['company_id'], unique=False)

    # 11. venture_initialization_plans
    op.create_table(
        'venture_initialization_plans',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('target_structure', sa.String(length=32), nullable=False, server_default='NEW_COMPANY'),
        sa.Column('departments_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('workforce_plan_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('product_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('financial_setup_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_initialization_plans_company_id', 'venture_initialization_plans', ['company_id'], unique=False)

    # 12. venture_resource_requests
    op.create_table(
        'venture_resource_requests',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('workforce_count', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('model_budget_usd', sa.Integer(), nullable=False, server_default='500000'),
        sa.Column('storage_gb', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('compute_cores', sa.Integer(), nullable=False, server_default='16'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_resource_requests_company_id', 'venture_resource_requests', ['company_id'], unique=False)

    # 13. venture_launch_readiness_records
    op.create_table(
        'venture_launch_readiness_records',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('product_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('technical_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('security_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('financial_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('governance_ready', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='NOT_READY'),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_launch_readiness_company_id', 'venture_launch_readiness_records', ['company_id'], unique=False)

    # 14. venture_outcomes
    op.create_table(
        'venture_outcomes',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('venture_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('expected_outcomes_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('actual_outcomes_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('variance_analysis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='INITIAL'),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venture_outcomes_company_id', 'venture_outcomes', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_table('venture_outcomes')
    op.drop_table('venture_launch_readiness_records')
    op.drop_table('venture_resource_requests')
    op.drop_table('venture_initialization_plans')
    op.drop_table('venture_proposals')
    op.drop_table('innovation_reviews')
    op.drop_table('venture_experiments')
    op.drop_table('venture_validations')
    op.drop_table('venture_business_cases')
    op.drop_table('business_model_concepts')
    op.drop_table('product_concepts')
    op.drop_table('business_hypotheses')
    op.drop_table('innovation_ideas')
    op.drop_table('innovation_opportunities')
