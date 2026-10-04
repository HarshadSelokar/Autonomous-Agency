"""Create Phase 23 Business Operations & Financial Operations Tables

Revision ID: 022
Revises: 021
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. business_accounts
    op.create_table(
        'business_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('balance_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. business_transactions
    op.create_table(
        'business_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('counterparty', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='INTERNAL'),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='RECORDED'),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('reconciliation_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. revenue_records
    op.create_table(
        'revenue_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('product_service', sa.String(length=255), nullable=False),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('period_id', sa.String(length=36), nullable=True),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('recognition_state', sa.String(length=50), nullable=False, server_default='EXPECTED'),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. expense_records
    op.create_table(
        'expense_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('vendor_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('incurred_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('employee_id', sa.String(length=36), nullable=True),
        sa.Column('purchase_order_id', sa.String(length=36), nullable=True),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('approval_state', sa.String(length=50), nullable=False, server_default='REQUESTED'),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('reconciliation_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('issuer_name', sa.String(length=255), nullable=False),
        sa.Column('subtotal_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('tax_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('governance_approval_id', sa.String(length=36), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. invoice_lines
    op.create_table(
        'invoice_lines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('subtotal_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. payments
    op.create_table(
        'payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='BANK_TRANSFER'),
        sa.Column('counterparty', sa.String(length=255), nullable=False),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='EXPECTED'),
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('governance_approval_id', sa.String(length=36), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('evidence_reference', sa.Text(), nullable=True),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('vendor_id', sa.String(length=36), nullable=True),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('plan_name', sa.String(length=100), nullable=False),
        sa.Column('amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('billing_interval', sa.String(length=50), nullable=False, server_default='MONTHLY'),
        sa.Column('renewal_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('cancellation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. orders
    op.create_table(
        'orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('order_number', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=36), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('total_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CREATED'),
        sa.Column('fulfillment_reference', sa.String(length=255), nullable=True),
        sa.Column('invoice_id', sa.String(length=36), nullable=True),
        sa.Column('payment_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. customer_accounts
    op.create_table(
        'customer_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('credit_limit_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. vendors
    op.create_table(
        'vendors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('categories_json', JSON(), nullable=True),
        sa.Column('payment_terms', sa.String(length=50), nullable=False, server_default='NET_30'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('risk_level', sa.String(length=50), nullable=False, server_default='LOW'),
        sa.Column('bank_details_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. procurement_requests
    op.create_table(
        'procurement_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('requester_id', sa.String(length=36), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('vendor_id', sa.String(length=36), nullable=True),
        sa.Column('item_description', sa.Text(), nullable=False),
        sa.Column('estimated_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='REQUESTED'),
        sa.Column('approval_governance_id', sa.String(length=36), nullable=True),
        sa.Column('approver_id', sa.String(length=36), nullable=True),
        sa.Column('purchase_order_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. purchase_orders
    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('po_number', sa.String(length=100), nullable=False),
        sa.Column('procurement_request_id', sa.String(length=36), nullable=False),
        sa.Column('vendor_id', sa.String(length=36), nullable=False),
        sa.Column('requester_id', sa.String(length=36), nullable=False),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('total_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ISSUED'),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 14. budgets
    op.create_table(
        'budgets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('company_id', sa.String(length=36), nullable=False, server_default='DEFAULT'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('period_name', sa.String(length=50), nullable=False, server_default='Q3-2026'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('allocated_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('consumed_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 15. budget_allocations
    op.create_table(
        'budget_allocations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('budget_id', sa.String(length=36), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('allocated_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('consumed_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('department_id', sa.String(length=36), nullable=True),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. financial_periods
    op.create_table(
        'financial_periods',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('period_name', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_by', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. reconciliations
    op.create_table(
        'reconciliations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('period_id', sa.String(length=36), nullable=True),
        sa.Column('source_provider', sa.String(length=100), nullable=False, server_default='EXTERNAL_BANK'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('total_matched_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_mismatched_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('conducted_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 18. reconciliation_items
    op.create_table(
        'reconciliation_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('reconciliation_id', sa.String(length=36), nullable=False),
        sa.Column('internal_ref', sa.String(length=255), nullable=False),
        sa.Column('external_ref', sa.String(length=255), nullable=False),
        sa.Column('internal_amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('external_amount_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('discrepancy_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 19. cash_flow_snapshots
    op.create_table(
        'cash_flow_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='USD'),
        sa.Column('actual_inflow_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('actual_outflow_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('expected_inflow_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('expected_outflow_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('committed_spending_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('available_budget_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )

    # 20. business_metrics
    op.create_table(
        'business_metrics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('value_cents', sa.BigInteger(), nullable=True),
        sa.Column('numeric_value', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default='USD'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('provenance_references_json', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 21. business_processes
    op.create_table(
        'business_processes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('process_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DEFINED'),
        sa.Column('associated_task_ids_json', JSON(), nullable=True),
        sa.Column('step_history_json', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('business_processes')
    op.drop_table('business_metrics')
    op.drop_table('cash_flow_snapshots')
    op.drop_table('reconciliation_items')
    op.drop_table('reconciliations')
    op.drop_table('financial_periods')
    op.drop_table('budget_allocations')
    op.drop_table('budgets')
    op.drop_table('purchase_orders')
    op.drop_table('procurement_requests')
    op.drop_table('vendors')
    op.drop_table('customer_accounts')
    op.drop_table('orders')
    op.drop_table('subscriptions')
    op.drop_table('payments')
    op.drop_table('invoice_lines')
    op.drop_table('invoices')
    op.drop_table('expense_records')
    op.drop_table('revenue_records')
    op.drop_table('business_transactions')
    op.drop_table('business_accounts')
