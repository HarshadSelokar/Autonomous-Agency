"""create phase15 dynamic workforce tables

Revision ID: 017
Revises: 016
Create Date: 2026-09-15 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '017'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. workforce_demands
    op.create_table(
        'workforce_demands',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('source_id', sa.String(length=64), nullable=False),
        sa.Column('department_id', sa.String(length=64), nullable=True),
        sa.Column('capability', sa.String(length=64), nullable=False),
        sa.Column('required_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('duration_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('risk_level', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('governance_required', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workforce_demands_source_id', 'workforce_demands', ['source_id'])
    op.create_index('ix_workforce_demands_department_id', 'workforce_demands', ['department_id'])
    op.create_index('ix_workforce_demands_capability', 'workforce_demands', ['capability'])

    # 2. capacity_snapshots
    op.create_table(
        'capacity_snapshots',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('employee_id', sa.String(length=64), nullable=False),
        sa.Column('capability', sa.String(length=64), nullable=False),
        sa.Column('max_capacity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('allocated_capacity', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('available_capacity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('active_assignments_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('snapshot_time', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_capacity_snapshots_employee_id', 'capacity_snapshots', ['employee_id'])
    op.create_index('ix_capacity_snapshots_capability', 'capacity_snapshots', ['capability'])

    # 3. capability_gaps
    op.create_table(
        'capability_gaps',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('capability', sa.String(length=64), nullable=False),
        sa.Column('required_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('available_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gap_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('affected_project_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_capability_gaps_capability', 'capability_gaps', ['capability'])

    # 4. staffing_recommendations
    op.create_table(
        'staffing_recommendations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('demand_id', sa.String(length=64), nullable=False),
        sa.Column('candidate_employee_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('capability_fit_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('availability_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('workload_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reliability_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('context_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('penalty_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('final_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reasoning', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_staffing_recommendations_demand_id', 'staffing_recommendations', ['demand_id'])

    # 5. workforce_allocations
    op.create_table(
        'workforce_allocations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('employee_id', sa.String(length=64), nullable=False),
        sa.Column('team_id', sa.String(length=64), nullable=True),
        sa.Column('project_id', sa.String(length=64), nullable=True),
        sa.Column('department_id', sa.String(length=64), nullable=True),
        sa.Column('allocation_percentage', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('is_temporary', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workforce_allocations_employee_id', 'workforce_allocations', ['employee_id'])
    op.create_index('ix_workforce_allocations_team_id', 'workforce_allocations', ['team_id'])

    # 6. workforce_change_requests
    op.create_table(
        'workforce_change_requests',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('request_type', sa.String(length=64), nullable=False),
        sa.Column('target_id', sa.String(length=64), nullable=False),
        sa.Column('requested_by_id', sa.String(length=64), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('governance_approval_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. workforce_decisions
    op.create_table(
        'workforce_decisions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('change_request_id', sa.String(length=64), nullable=True),
        sa.Column('recommendation_id', sa.String(length=64), nullable=True),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('manager_id', sa.String(length=64), nullable=True),
        sa.Column('human_approver_id', sa.String(length=64), nullable=True),
        sa.Column('decision_type', sa.String(length=32), nullable=False, server_default='APPROVED'),
        sa.Column('reason', sa.Text(), nullable=False, server_default=''),
        sa.Column('policy_applied', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. employee_templates
    op.create_table(
        'employee_templates',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=64), nullable=False),
        sa.Column('capabilities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('skills_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('responsibilities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('default_permissions_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('department_compatibility_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('governance_requirements_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('default_agent_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. workforce_plans
    op.create_table(
        'workforce_plans',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('planning_horizon', sa.String(length=32), nullable=False, server_default='Q1'),
        sa.Column('objectives_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('demand_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('capacity_snapshot_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('gap_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('recommendation_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. teams
    op.create_table(
        'teams',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=False, server_default=''),
        sa.Column('team_type', sa.String(length=32), nullable=False, server_default='TEMPORARY'),
        sa.Column('project_id', sa.String(length=64), nullable=True),
        sa.Column('department_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('manager_id', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('capabilities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('creation_reason', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dissolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_teams_code', 'teams', ['code'])
    op.create_index('ix_teams_project_id', 'teams', ['project_id'])

    # 11. team_members
    op.create_table(
        'team_members',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('team_id', sa.String(length=64), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', sa.String(length=64), nullable=False),
        sa.Column('role_in_team', sa.String(length=64), nullable=False, server_default='MEMBER'),
        sa.Column('allocation_percentage', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_employee_id', 'team_members', ['employee_id'])


def downgrade() -> None:
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('workforce_plans')
    op.drop_table('employee_templates')
    op.drop_table('workforce_decisions')
    op.drop_table('workforce_change_requests')
    op.drop_table('workforce_allocations')
    op.drop_table('staffing_recommendations')
    op.drop_table('capability_gaps')
    op.drop_table('capacity_snapshots')
    op.drop_table('workforce_demands')
