"""Create Phase 19 Research, Discovery & Innovation Tables

Revision ID: 020
Revises: 019
Create Date: 2026-09-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

# revision identifiers, used by Alembic.
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. research_programs
    op.create_table(
        'research_programs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False, server_default='COMPANY'),
        sa.Column('owner_id', sa.String(length=36), nullable=False, server_default='system'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('research_question_ids', JSON(), nullable=True),
        sa.Column('findings_ids', JSON(), nullable=True),
        sa.Column('knowledge_item_ids', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. research_requests
    op.create_table(
        'research_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False, server_default='COMPANY'),
        sa.Column('urgency', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('requester_id', sa.String(length=36), nullable=False, server_default='system'),
        sa.Column('source_origin', sa.String(length=50), nullable=False, server_default='STRATEGY'),
        sa.Column('expected_output', sa.Text(), nullable=False, server_default=''),
        sa.Column('constraints', JSON(), nullable=True),
        sa.Column('evidence_requirements', JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='REQUESTED'),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. research_questions
    op.create_table(
        'research_questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=False, server_default=''),
        sa.Column('assumptions', JSON(), nullable=True),
        sa.Column('scope', sa.String(length=50), nullable=False, server_default='COMPANY'),
        sa.Column('evidence_requirements', JSON(), nullable=True),
        sa.Column('success_criteria', JSON(), nullable=True),
        sa.Column('parent_question_id', sa.String(length=36), nullable=True),
        sa.Column('sub_question_ids', JSON(), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False, server_default='system'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. research_plans
    op.create_table(
        'research_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False, server_default=''),
        sa.Column('task_ids', JSON(), nullable=True),
        sa.Column('assigned_employee_ids', JSON(), nullable=True),
        sa.Column('assigned_team_id', sa.String(length=36), nullable=True),
        sa.Column('tool_requirements', JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. research_sources
    op.create_table(
        'research_sources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('location', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='INTERNAL_DOCUMENT'),
        sa.Column('access_method', sa.String(length=50), nullable=False, server_default='READ'),
        sa.Column('provenance', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_external', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_untrusted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('prompt_injection_checked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reliability_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. research_evidence
    op.create_table(
        'research_evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_id', sa.String(length=36), nullable=False),
        sa.Column('content_snippet', sa.Text(), nullable=False, server_default=''),
        sa.Column('data_points', JSON(), nullable=True),
        sa.Column('integrity_hash', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('is_independent', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('corroboration_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. research_findings
    op.create_table(
        'research_findings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('finding_statement', sa.Text(), nullable=False),
        sa.Column('evidence_ids', JSON(), nullable=True),
        sa.Column('scope', sa.String(length=50), nullable=False, server_default='COMPANY'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('assumptions', JSON(), nullable=True),
        sa.Column('limitations', JSON(), nullable=True),
        sa.Column('researcher_id', sa.String(length=36), nullable=False, server_default='system'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. research_hypotheses
    op.create_table(
        'research_hypotheses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('observation', sa.Text(), nullable=False, server_default=''),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('prediction', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PROPOSED'),
        sa.Column('experiment_id', sa.String(length=36), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('conclusion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. research_benchmarks
    op.create_table(
        'research_benchmarks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('benchmark_type', sa.String(length=50), nullable=False, server_default='MODEL_PERFORMANCE'),
        sa.Column('target_name', sa.String(length=255), nullable=False),
        sa.Column('workload_description', sa.Text(), nullable=False, server_default=''),
        sa.Column('metrics', JSON(), nullable=True),
        sa.Column('environment', sa.String(length=100), nullable=False, server_default='TEST'),
        sa.Column('limitations', JSON(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. technology_evaluations
    op.create_table(
        'technology_evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_technology', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='FRAMEWORK'),
        sa.Column('benchmark_ids', JSON(), nullable=True),
        sa.Column('security_review_summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('cost_analysis', JSON(), nullable=True),
        sa.Column('operational_feasibility', sa.Text(), nullable=False, server_default=''),
        sa.Column('recommendation', sa.Text(), nullable=False, server_default=''),
        sa.Column('governance_approval_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. research_discoveries
    op.create_table(
        'research_discoveries',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('trigger_event', sa.String(length=100), nullable=False),
        sa.Column('trigger_entity_id', sa.String(length=36), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_request_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. research_opportunities
    op.create_table(
        'research_opportunities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('finding_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='IDENTIFIED'),
        sa.Column('estimated_value_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. innovation_proposals
    op.create_table(
        'innovation_proposals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('innovation_type', sa.String(length=50), nullable=False, server_default='TECHNOLOGY_INNOVATION'),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('evidence_ids', JSON(), nullable=True),
        sa.Column('proposed_solution', sa.Text(), nullable=False),
        sa.Column('expected_value', sa.Text(), nullable=False, server_default=''),
        sa.Column('required_capabilities', JSON(), nullable=True),
        sa.Column('required_resources', JSON(), nullable=True),
        sa.Column('risks', JSON(), nullable=True),
        sa.Column('reversibility', sa.String(length=50), nullable=False, server_default='HIGH'),
        sa.Column('governance_request_id', sa.String(length=36), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('strategic_initiative_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('innovation_proposals')
    op.drop_table('research_opportunities')
    op.drop_table('research_discoveries')
    op.drop_table('technology_evaluations')
    op.drop_table('research_benchmarks')
    op.drop_table('research_hypotheses')
    op.drop_table('research_findings')
    op.drop_table('research_evidence')
    op.drop_table('research_sources')
    op.drop_table('research_plans')
    op.drop_table('research_questions')
    op.drop_table('research_requests')
    op.drop_table('research_programs')
