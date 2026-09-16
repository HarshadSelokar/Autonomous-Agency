"""create phase18 institutional knowledge tables

Revision ID: 019
Revises: 018
Create Date: 2026-09-16 22:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '019'
down_revision: Union[str, None] = '018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. knowledge_items
    op.create_table(
        'knowledge_items',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('knowledge_type', sa.String(length=64), nullable=False, server_default='FACT'),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('scope_id', sa.String(length=64), nullable=True),
        sa.Column('authority', sa.String(length=32), nullable=False, server_default='UNVERIFIED'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='CANDIDATE'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('owner_id', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_items_knowledge_type', 'knowledge_items', ['knowledge_type'])
    op.create_index('ix_knowledge_items_scope', 'knowledge_items', ['scope'])
    op.create_index('ix_knowledge_items_authority', 'knowledge_items', ['authority'])
    op.create_index('ix_knowledge_items_status', 'knowledge_items', ['status'])

    # 2. knowledge_claims
    op.create_table(
        'knowledge_claims',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('knowledge_id', sa.String(length=64), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('claim_scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('source_type', sa.String(length=64), nullable=False, server_default='TASK_EXECUTION'),
        sa.Column('source_id', sa.String(length=64), nullable=False),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('authority', sa.String(length=32), nullable=False, server_default='UNVERIFIED'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='CANDIDATE'),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_claims_knowledge_id', 'knowledge_claims', ['knowledge_id'])

    # 3. knowledge_provenances
    op.create_table(
        'knowledge_provenances',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('knowledge_id', sa.String(length=64), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False, server_default='TASK'),
        sa.Column('source_id', sa.String(length=64), nullable=False),
        sa.Column('employee_id', sa.String(length=64), nullable=True),
        sa.Column('agent_id', sa.String(length=64), nullable=True),
        sa.Column('task_id', sa.String(length=64), nullable=True),
        sa.Column('project_id', sa.String(length=64), nullable=True),
        sa.Column('objective_id', sa.String(length=64), nullable=True),
        sa.Column('decision_id', sa.String(length=64), nullable=True),
        sa.Column('meeting_id', sa.String(length=64), nullable=True),
        sa.Column('artifact_id', sa.String(length=64), nullable=True),
        sa.Column('verification_id', sa.String(length=64), nullable=True),
        sa.Column('outcome_id', sa.String(length=64), nullable=True),
        sa.Column('memory_id', sa.String(length=64), nullable=True),
        sa.Column('analysis_id', sa.String(length=64), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_provenances_knowledge_id', 'knowledge_provenances', ['knowledge_id'])

    # 4. knowledge_validations
    op.create_table(
        'knowledge_validations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('knowledge_id', sa.String(length=64), nullable=False),
        sa.Column('validator_id', sa.String(length=64), nullable=False, server_default='system_validator'),
        sa.Column('validator_type', sa.String(length=64), nullable=False, server_default='DETERMINISTIC_VERIFICATION'),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('validation_status', sa.String(length=32), nullable=False, server_default='PASSED'),
        sa.Column('confidence_delta', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('rationale', sa.Text(), nullable=False, server_default=''),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_validations_knowledge_id', 'knowledge_validations', ['knowledge_id'])

    # 5. knowledge_conflicts
    op.create_table(
        'knowledge_conflicts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('knowledge_id_a', sa.String(length=64), nullable=False),
        sa.Column('knowledge_id_b', sa.String(length=64), nullable=False),
        sa.Column('conflict_type', sa.String(length=64), nullable=False, server_default='CONTRADICTORY_STATEMENT'),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPEN'),
        sa.Column('resolution_strategy', sa.Text(), nullable=True),
        sa.Column('resolved_by_id', sa.String(length=64), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_conflicts_knowledge_id_a', 'knowledge_conflicts', ['knowledge_id_a'])
    op.create_index('ix_knowledge_conflicts_knowledge_id_b', 'knowledge_conflicts', ['knowledge_id_b'])
    op.create_index('ix_knowledge_conflicts_status', 'knowledge_conflicts', ['status'])

    # 6. knowledge_relationships
    op.create_table(
        'knowledge_relationships',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False, server_default='KNOWLEDGE'),
        sa.Column('source_id', sa.String(length=64), nullable=False),
        sa.Column('target_type', sa.String(length=64), nullable=False, server_default='KNOWLEDGE'),
        sa.Column('target_id', sa.String(length=64), nullable=False),
        sa.Column('relationship_type', sa.String(length=64), nullable=False, server_default='LEADS_TO_LESSON'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_relationships_source_id', 'knowledge_relationships', ['source_id'])
    op.create_index('ix_knowledge_relationships_target_id', 'knowledge_relationships', ['target_id'])
    op.create_index('ix_knowledge_relationships_relationship_type', 'knowledge_relationships', ['relationship_type'])

    # 7. knowledge_procedures
    op.create_table(
        'knowledge_procedures',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False, server_default=''),
        sa.Column('prerequisites_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('steps_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('expected_outcome', sa.Text(), nullable=False, server_default=''),
        sa.Column('verification_criteria_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('failure_conditions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('rollback_steps_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('owner_id', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('validation_status', sa.String(length=32), nullable=False, server_default='CANDIDATE'),
        sa.Column('is_governance_approved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. organizational_experiments
    op.create_table(
        'organizational_experiments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('hypothesis', sa.Text(), nullable=False),
        sa.Column('objective_id', sa.String(length=64), nullable=True),
        sa.Column('scope', sa.String(length=32), nullable=False, server_default='COMPANY'),
        sa.Column('scope_id', sa.String(length=64), nullable=True),
        sa.Column('baseline_metrics_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('treatment_params_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('success_criteria_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('risk_level', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('duration_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('results_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('conclusion', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_isolated', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. knowledge_usage_records
    op.create_table(
        'knowledge_usage_records',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('knowledge_id', sa.String(length=64), nullable=False),
        sa.Column('consumer_id', sa.String(length=64), nullable=False),
        sa.Column('task_id', sa.String(length=64), nullable=True),
        sa.Column('context_scope', sa.String(length=64), nullable=False, server_default='TASK_EXECUTION'),
        sa.Column('outcome_status', sa.String(length=32), nullable=False, server_default='SUCCESS'),
        sa.Column('effectiveness_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_usage_records_knowledge_id', 'knowledge_usage_records', ['knowledge_id'])


def downgrade() -> None:
    op.drop_table('knowledge_usage_records')
    op.drop_table('organizational_experiments')
    op.drop_table('knowledge_procedures')
    op.drop_table('knowledge_relationships')
    op.drop_table('knowledge_conflicts')
    op.drop_table('knowledge_validations')
    op.drop_table('knowledge_provenances')
    op.drop_table('knowledge_claims')
    op.drop_table('knowledge_items')
