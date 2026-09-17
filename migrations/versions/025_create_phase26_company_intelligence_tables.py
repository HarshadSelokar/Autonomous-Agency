"""create phase26 company intelligence tables

Revision ID: 025
Revises: 024
Create Date: 2026-09-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '025'
down_revision: Union[str, None] = '024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. intelligence_runs
    op.create_table(
        'intelligence_runs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('purpose', sa.String(length=256), nullable=False),
        sa.Column('scope', sa.String(length=64), nullable=False, server_default='FULL_COMPANY'),
        sa.Column('environment', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
        sa.Column('simulation_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='REQUESTED'),
        sa.Column('requesting_principal', sa.String(length=64), nullable=False, server_default='SYSTEM'),
        sa.Column('data_sources_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('model_metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('findings_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('uncertainty_score', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_runs_company_id', 'intelligence_runs', ['company_id'], unique=False)

    # 2. intelligence_findings
    op.create_table(
        'intelligence_findings',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('observation_summary', sa.Text(), nullable=False),
        sa.Column('evidence_references_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.9'),
        sa.Column('is_anomaly', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intelligence_findings_company_id', 'intelligence_findings', ['company_id'], unique=False)
    op.create_index('ix_intelligence_findings_run_id', 'intelligence_findings', ['run_id'], unique=False)

    # 3. decision_questions
    op.create_table(
        'decision_questions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('purpose', sa.String(length=256), nullable=False),
        sa.Column('scope', sa.String(length=64), nullable=False, server_default='STRATEGIC'),
        sa.Column('urgency', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('requester_id', sa.String(length=64), nullable=False, server_default='SYSTEM'),
        sa.Column('constraints_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('decision_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_questions_company_id', 'decision_questions', ['company_id'], unique=False)

    # 4. decision_options
    op.create_table(
        'decision_options',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('question_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('option_name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_no_action_baseline', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('required_resources_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('expected_benefits_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('expected_costs_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('risk_factors_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('dependencies_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('scenario_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_options_question_id', 'decision_options', ['question_id'], unique=False)
    op.create_index('ix_decision_options_company_id', 'decision_options', ['company_id'], unique=False)

    # 5. decision_evaluations
    op.create_table(
        'decision_evaluations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('option_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('strategic_alignment_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('financial_impact_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('customer_impact_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('product_impact_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('workforce_impact_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('operational_risk_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('execution_complexity_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('reversibility_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('evaluation_breakdown_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_evaluations_option_id', 'decision_evaluations', ['option_id'], unique=False)

    # 6. decision_insights
    op.create_table(
        'decision_insights',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('question_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('evidence_graph_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('options_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('tradeoffs_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('recommendation_summary', sa.Text(), nullable=False),
        sa.Column('recommended_option_id', sa.String(length=64), nullable=True),
        sa.Column('uncertainty_analysis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('is_executed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_expired', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_insights_question_id', 'decision_insights', ['question_id'], unique=False)
    op.create_index('ix_decision_insights_company_id', 'decision_insights', ['company_id'], unique=False)

    # 7. company_health_assessments
    op.create_table(
        'company_health_assessments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('overall_health_status', sa.String(length=32), nullable=False, server_default='HEALTHY'),
        sa.Column('dimension_scores_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('key_findings_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('top_risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('top_opportunities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_health_company_id', 'company_health_assessments', ['company_id'], unique=False)

    # 8. company_bottlenecks
    op.create_table(
        'company_bottlenecks',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('bottleneck_name', sa.String(length=128), nullable=False),
        sa.Column('affected_scope', sa.String(length=128), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('evidence_summary', sa.Text(), nullable=False),
        sa.Column('suspected_causes_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_bottlenecks_company_id', 'company_bottlenecks', ['company_id'], unique=False)

    # 9. company_risk_assessments
    op.create_table(
        'company_risk_assessments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False, server_default='OPERATIONAL'),
        sa.Column('probability_score', sa.Float(), nullable=False, server_default='0.3'),
        sa.Column('impact_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('leading_indicators_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('mitigation_options_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_company_risks_company_id', 'company_risk_assessments', ['company_id'], unique=False)

    # 10. decision_outcome_evaluations
    op.create_table(
        'decision_outcome_evaluations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('insight_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('executed_option_id', sa.String(length=64), nullable=False),
        sa.Column('expected_outcomes_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('actual_outcomes_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('variance_analysis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('learning_candidate', sa.Text(), nullable=False),
        sa.Column('knowledge_item_id', sa.String(length=64), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_decision_outcomes_company_id', 'decision_outcome_evaluations', ['company_id'], unique=False)
    op.create_index('ix_decision_outcomes_insight_id', 'decision_outcome_evaluations', ['insight_id'], unique=False)


def downgrade() -> None:
    op.drop_table('decision_outcome_evaluations')
    op.drop_table('company_risk_assessments')
    op.drop_table('company_bottlenecks')
    op.drop_table('company_health_assessments')
    op.drop_table('decision_insights')
    op.drop_table('decision_evaluations')
    op.drop_table('decision_options')
    op.drop_table('decision_questions')
    op.drop_table('intelligence_findings')
    op.drop_table('intelligence_runs')
