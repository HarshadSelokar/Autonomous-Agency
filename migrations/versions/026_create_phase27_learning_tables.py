"""create phase27 learning and adaptation tables

Revision ID: 026
Revises: 025
Create Date: 2026-09-17 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '026'
down_revision: Union[str, None] = '025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. learning_cycles
    op.create_table(
        'learning_cycles',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('purpose', sa.String(length=256), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('environment', sa.String(length=32), nullable=False, server_default='PRODUCTION'),
        sa.Column('simulation_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='CREATED'),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('observations_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('patterns_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_cycles_company_id', 'learning_cycles', ['company_id'], unique=False)

    # 2. learning_observations
    op.create_table(
        'learning_observations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('cycle_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('source_subsystem', sa.String(length=64), nullable=False),
        sa.Column('entity_reference', sa.String(length=128), nullable=False),
        sa.Column('observed_value_json', sa.Text(), nullable=True),
        sa.Column('expected_value_json', sa.Text(), nullable=True),
        sa.Column('context_data_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('provenance_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_observations_company_id', 'learning_observations', ['company_id'], unique=False)
    op.create_index('ix_learning_observations_cycle_id', 'learning_observations', ['cycle_id'], unique=False)

    # 3. expected_vs_actual_comparisons
    op.create_table(
        'expected_vs_actual_comparisons',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('cycle_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('metric_name', sa.String(length=128), nullable=False),
        sa.Column('expected_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('actual_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('variance', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('variance_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.9'),
        sa.Column('context_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_expected_vs_actual_company_id', 'expected_vs_actual_comparisons', ['company_id'], unique=False)

    # 4. learning_candidates
    op.create_table(
        'learning_candidates',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('cycle_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('supporting_observation_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('counterexamples_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('assumptions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('generated_by', sa.String(length=64), nullable=False, server_default='SYSTEM'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_candidates_company_id', 'learning_candidates', ['company_id'], unique=False)

    # 5. learning_validations
    op.create_table(
        'learning_validations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('candidate_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('validation_method', sa.String(length=64), nullable=False, server_default='HISTORICAL_ANALYSIS'),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('evidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('validation_notes', sa.Text(), nullable=False, server_default=''),
        sa.Column('validated_by', sa.String(length=64), nullable=False, server_default='SYSTEM'),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_validations_company_id', 'learning_validations', ['company_id'], unique=False)

    # 6. learning_conflicts
    op.create_table(
        'learning_conflicts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('lesson_a_id', sa.String(length=64), nullable=False),
        sa.Column('lesson_b_id', sa.String(length=64), nullable=False),
        sa.Column('conflict_summary', sa.Text(), nullable=False),
        sa.Column('context_discrepancies_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPEN'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_conflicts_company_id', 'learning_conflicts', ['company_id'], unique=False)

    # 7. learning_patterns
    op.create_table(
        'learning_patterns',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('pattern_name', sa.String(length=128), nullable=False),
        sa.Column('pattern_type', sa.String(length=64), nullable=False, server_default='RECURRING_FAILURE'),
        sa.Column('frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.85'),
        sa.Column('evidence_references_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_learning_patterns_company_id', 'learning_patterns', ['company_id'], unique=False)

    # 8. improvement_opportunities
    op.create_table(
        'improvement_opportunities',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('affected_area', sa.String(length=128), nullable=False),
        sa.Column('expected_impact', sa.Text(), nullable=False),
        sa.Column('required_resources_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('risks_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('constraints_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('identified_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_improvement_opportunities_company_id', 'improvement_opportunities', ['company_id'], unique=False)

    # 9. adaptation_proposals
    op.create_table(
        'adaptation_proposals',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('opportunity_id', sa.String(length=64), nullable=False),
        sa.Column('adaptation_type', sa.String(length=64), nullable=False, server_default='WORKFLOW_CHANGE'),
        sa.Column('risk_level', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('current_state_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('proposed_state_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('rollback_plan_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_adaptation_proposals_company_id', 'adaptation_proposals', ['company_id'], unique=False)

    # 10. adaptation_evaluations
    op.create_table(
        'adaptation_evaluations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('expected_benefit_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('cost_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('reversibility_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('overall_recommendation_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('evaluation_breakdown_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_adaptation_evaluations_company_id', 'adaptation_evaluations', ['company_id'], unique=False)

    # 11. adaptation_executions
    op.create_table(
        'adaptation_executions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=False),
        sa.Column('execution_type', sa.String(length=64), nullable=False, server_default='CONTROLLED_EXPERIMENT'),
        sa.Column('target_subsystem', sa.String(length=64), nullable=False),
        sa.Column('execution_payload_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_adaptation_executions_company_id', 'adaptation_executions', ['company_id'], unique=False)

    # 12. adaptation_outcomes
    op.create_table(
        'adaptation_outcomes',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('execution_id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('expected_metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('actual_metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('variance_analysis_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('side_effects_detected_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('has_regression', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_adaptation_outcomes_company_id', 'adaptation_outcomes', ['company_id'], unique=False)

    # 13. adaptation_impact_assessments
    op.create_table(
        'adaptation_impact_assessments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('proposal_id', sa.String(length=64), nullable=False),
        sa.Column('company_id', sa.String(length=64), nullable=False),
        sa.Column('affected_subsystems_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('downstream_dependencies_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('rollback_feasibility_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_adaptation_impact_company_id', 'adaptation_impact_assessments', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_table('adaptation_impact_assessments')
    op.drop_table('adaptation_outcomes')
    op.drop_table('adaptation_executions')
    op.drop_table('adaptation_evaluations')
    op.drop_table('adaptation_proposals')
    op.drop_table('improvement_opportunities')
    op.drop_table('learning_patterns')
    op.drop_table('learning_conflicts')
    op.drop_table('learning_validations')
    op.drop_table('learning_candidates')
    op.drop_table('expected_vs_actual_comparisons')
    op.drop_table('learning_observations')
    op.drop_table('learning_cycles')
