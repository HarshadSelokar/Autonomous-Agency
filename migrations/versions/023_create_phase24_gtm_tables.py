"""Create Phase 24 Product, Customer & GTM Operations Tables

Revision ID: 023
Revises: 022
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. products
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='SOFTWARE'),
        sa.Column('lifecycle', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('owner_employee_id', sa.String(length=36), nullable=False),
        sa.Column('target_market', sa.String(length=100), nullable=False, server_default='ENTERPRISE'),
        sa.Column('base_price_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. product_versions
    op.create_table(
        'product_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('version_string', sa.String(length=50), nullable=False),
        sa.Column('release_notes', sa.Text(), nullable=False),
        sa.Column('is_released', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('release_date', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. product_roadmaps
    op.create_table(
        'product_roadmaps',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('target_period', sa.String(length=50), nullable=False),
        sa.Column('objectives_json', JSON(), nullable=True),
        sa.Column('priorities_json', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. product_requirements
    op.create_table(
        'product_requirements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('user_story', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('source_feedback_id', sa.String(length=36), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PROPOSED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. product_feedback
    op.create_table(
        'product_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='FEATURE_REQUEST'),
        sa.Column('summary', sa.String(length=255), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('importance_score', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('validated_insight', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='RECEIVED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('segment', sa.String(length=100), nullable=False, server_default='ENTERPRISE'),
        sa.Column('lifecycle_state', sa.String(length=50), nullable=False, server_default='PROSPECT'),
        sa.Column('account_manager_id', sa.String(length=36), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. customer_contacts
    op.create_table(
        'customer_contacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. customer_interactions
    op.create_table(
        'customer_interactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('contact_id', sa.String(length=36), nullable=True),
        sa.Column('interaction_type', sa.String(length=50), nullable=False, server_default='EMAIL'),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='EXTERNAL_CUSTOMER'),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('provenance_reference', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. customer_health_snapshots
    op.create_table(
        'customer_health_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('product_usage_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('open_support_cases', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('satisfaction_score', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='HEALTHY'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. customer_outcomes
    op.create_table(
        'customer_outcomes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('goal_description', sa.Text(), nullable=False),
        sa.Column('measured_outcome', sa.Text(), nullable=False),
        sa.Column('verified_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('achieved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. leads
    op.create_table(
        'leads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='INBOUND_WEB'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='NEW'),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('assigned_owner_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. opportunities
    op.create_table(
        'opportunities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('lead_id', sa.String(length=36), nullable=True),
        sa.Column('customer_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False, server_default='IDENTIFIED'),
        sa.Column('estimated_value_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('probability_pct', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('expected_close_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. sales_activities
    op.create_table(
        'sales_activities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('performed_by', sa.String(length=36), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 14. proposals
    op.create_table(
        'proposals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('opportunity_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('product_id', sa.String(length=36), nullable=False),
        sa.Column('base_amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('discount_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('governance_approval_id', sa.String(length=36), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 15. customer_onboarding_plans
    op.create_table(
        'customer_onboarding_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('order_id', sa.String(length=36), nullable=True),
        sa.Column('milestones_json', JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('completion_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. support_cases
    op.create_table(
        'support_cases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('assigned_employee_id', sa.String(length=36), nullable=True),
        sa.Column('escalated_task_id', sa.String(length=36), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. marketing_campaigns
    op.create_table(
        'marketing_campaigns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('target_audience', sa.String(length=255), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='EMAIL'),
        sa.Column('budget_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('spent_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('governance_approval_id', sa.String(length=36), nullable=True),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 18. marketing_assets
    op.create_table(
        'marketing_assets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False, server_default='COPY_TEXT'),
        sa.Column('content_payload', sa.Text(), nullable=False),
        sa.Column('review_status', sa.String(length=50), nullable=False, server_default='PENDING_REVIEW'),
        sa.PrimaryKeyConstraint('id')
    )

    # 19. communication_preferences
    op.create_table(
        'communication_preferences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False, index=True),
        sa.Column('opt_in_marketing', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('opt_in_product_updates', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('opt_out_all', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 20. gtm_metrics
    op.create_table(
        'gtm_metrics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False, index=True),
        sa.Column('metric_value', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='COUNT'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('gtm_metrics')
    op.drop_table('communication_preferences')
    op.drop_table('marketing_assets')
    op.drop_table('marketing_campaigns')
    op.drop_table('support_cases')
    op.drop_table('customer_onboarding_plans')
    op.drop_table('proposals')
    op.drop_table('sales_activities')
    op.drop_table('opportunities')
    op.drop_table('leads')
    op.drop_table('customer_outcomes')
    op.drop_table('customer_health_snapshots')
    op.drop_table('customer_interactions')
    op.drop_table('customer_contacts')
    op.drop_table('customers')
    op.drop_table('product_feedback')
    op.drop_table('product_requirements')
    op.drop_table('product_roadmaps')
    op.drop_table('product_versions')
    op.drop_table('products')
