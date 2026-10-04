"""create phase14 department expansion tables

Revision ID: 016
Revises: 015
Create Date: 2026-09-15 22:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '016'
down_revision: Union[str, None] = '015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to departments table
    op.add_column('departments', sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'))
    op.add_column('departments', sa.Column('purpose', sa.Text(), nullable=False, server_default=''))
    op.add_column('departments', sa.Column('manager_employee_id', sa.String(length=64), nullable=True))
    op.add_column('departments', sa.Column('parent_department_id', sa.String(length=64), nullable=True))
    op.add_column('departments', sa.Column('capabilities_json', sa.Text(), nullable=False, server_default='[]'))
    op.add_column('departments', sa.Column('responsibilities_json', sa.Text(), nullable=False, server_default='[]'))
    op.add_column('departments', sa.Column('policies_json', sa.Text(), nullable=False, server_default='[]'))

    # Create department_requests table
    op.create_table(
        'department_requests',
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('requester_department_id', sa.String(length=64), nullable=False),
        sa.Column('receiving_department_id', sa.String(length=64), nullable=False),
        sa.Column('requester_employee_id', sa.String(length=64), nullable=False),
        sa.Column('receiving_manager_id', sa.String(length=64), nullable=False),
        sa.Column('delivery_owner_employee_id', sa.String(length=64), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=False),
        sa.Column('requested_outcome', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('required_capabilities_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='REQUESTED'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('related_objective_id', sa.String(length=64), nullable=True),
        sa.Column('related_project_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('request_id')
    )
    op.create_index(op.f('ix_department_requests_requester_department_id'), 'department_requests', ['requester_department_id'], unique=False)
    op.create_index(op.f('ix_department_requests_receiving_department_id'), 'department_requests', ['receiving_department_id'], unique=False)

    # Create department_handoffs table
    op.create_table(
        'department_handoffs',
        sa.Column('handoff_id', sa.String(length=64), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('sender_department_id', sa.String(length=64), nullable=False),
        sa.Column('receiver_department_id', sa.String(length=64), nullable=False),
        sa.Column('sender_employee_id', sa.String(length=64), nullable=False),
        sa.Column('expected_outcome', sa.Text(), nullable=False),
        sa.Column('artifact_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('evidence_ids_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PROPOSED'),
        sa.Column('acceptance_criteria_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('verification_id', sa.String(length=64), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('handoff_id')
    )
    op.create_index(op.f('ix_department_handoffs_request_id'), 'department_handoffs', ['request_id'], unique=False)

    # Create department_service_contracts table
    op.create_table(
        'department_service_contracts',
        sa.Column('contract_id', sa.String(length=64), nullable=False),
        sa.Column('provider_department_id', sa.String(length=64), nullable=False),
        sa.Column('consumer_department_id', sa.String(length=64), nullable=False),
        sa.Column('service_name', sa.String(length=128), nullable=False),
        sa.Column('input_schema_description', sa.Text(), nullable=False),
        sa.Column('expected_output_description', sa.Text(), nullable=False),
        sa.Column('acceptance_criteria_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('target_sla_seconds', sa.Integer(), nullable=False, server_default='86400'),
        sa.Column('required_approvals_json', sa.Text(), nullable=False, server_default='[]'),
        sa.PrimaryKeyConstraint('contract_id')
    )
    op.create_index(op.f('ix_department_service_contracts_provider_department_id'), 'department_service_contracts', ['provider_department_id'], unique=False)
    op.create_index(op.f('ix_department_service_contracts_consumer_department_id'), 'department_service_contracts', ['consumer_department_id'], unique=False)


def downgrade() -> None:
    op.drop_table('department_service_contracts')
    op.drop_table('department_handoffs')
    op.drop_table('department_requests')
    op.drop_column('departments', 'policies_json')
    op.drop_column('departments', 'responsibilities_json')
    op.drop_column('departments', 'capabilities_json')
    op.drop_column('departments', 'parent_department_id')
    op.drop_column('departments', 'manager_employee_id')
    op.drop_column('departments', 'purpose')
    op.drop_column('departments', 'status')
