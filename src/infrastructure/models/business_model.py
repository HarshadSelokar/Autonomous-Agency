"""
SQLAlchemy ORM models for Phase 23 Business Operations & Financial Operations.
"""

from datetime import UTC, datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON

from src.infrastructure.database import Base


class BusinessAccountModel(Base):
    __tablename__ = "business_accounts"

    id = Column(String(36), primary_key=True)
    account_code = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    balance_cents = Column(BigInteger, nullable=False, default=0)
    department_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class BusinessTransactionModel(Base):
    __tablename__ = "business_transactions"

    id = Column(String(36), primary_key=True)
    transaction_type = Column(String(50), nullable=False)
    amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    account_id = Column(String(36), nullable=False)
    counterparty = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False, default="INTERNAL")
    external_reference = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="RECORDED")
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    evidence_reference = Column(Text, nullable=True)
    verification_status = Column(String(50), nullable=False, default="UNVERIFIED")
    reconciliation_status = Column(String(50), nullable=False, default="PENDING")
    idempotency_key = Column(String(255), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)


class RevenueRecordModel(Base):
    __tablename__ = "revenue_records"

    id = Column(String(36), primary_key=True)
    source = Column(String(255), nullable=False)
    customer_id = Column(String(36), nullable=False)
    product_service = Column(String(255), nullable=False)
    amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    period_id = Column(String(36), nullable=True)
    invoice_id = Column(String(36), nullable=True)
    recognition_state = Column(String(50), nullable=False, default="EXPECTED")
    evidence_reference = Column(Text, nullable=True)
    verification_status = Column(String(50), nullable=False, default="UNVERIFIED")
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class ExpenseRecordModel(Base):
    __tablename__ = "expense_records"

    id = Column(String(36), primary_key=True)
    vendor_id = Column(String(36), nullable=False)
    category = Column(String(100), nullable=False)
    amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    incurred_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    project_id = Column(String(36), nullable=True)
    department_id = Column(String(36), nullable=True)
    employee_id = Column(String(36), nullable=True)
    purchase_order_id = Column(String(36), nullable=True)
    invoice_id = Column(String(36), nullable=True)
    approval_state = Column(String(50), nullable=False, default="REQUESTED")
    evidence_reference = Column(Text, nullable=True)
    verification_status = Column(String(50), nullable=False, default="UNVERIFIED")
    reconciliation_status = Column(String(50), nullable=False, default="PENDING")
    metadata_json = Column(JSON, nullable=True)


class InvoiceModel(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    customer_id = Column(String(36), nullable=False)
    issuer_name = Column(String(255), nullable=False, default="Autonomous AI Corp")
    subtotal_cents = Column(BigInteger, nullable=False, default=0)
    tax_cents = Column(BigInteger, nullable=False, default=0)
    total_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    issue_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    due_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    status = Column(String(50), nullable=False, default="DRAFT")
    evidence_reference = Column(Text, nullable=True)
    payment_reference = Column(String(255), nullable=True)
    governance_approval_id = Column(String(36), nullable=True)
    idempotency_key = Column(String(255), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)


class InvoiceLineModel(Base):
    __tablename__ = "invoice_lines"

    id = Column(String(36), primary_key=True)
    invoice_id = Column(String(36), nullable=False, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_cents = Column(BigInteger, nullable=False, default=0)
    subtotal_cents = Column(BigInteger, nullable=False, default=0)


class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True)
    invoice_id = Column(String(36), nullable=True)
    amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    payment_method = Column(String(50), nullable=False, default="BANK_TRANSFER")
    counterparty = Column(String(255), nullable=False)
    external_reference = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="EXPECTED")
    initiated_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    governance_approval_id = Column(String(36), nullable=True)
    idempotency_key = Column(String(255), nullable=True, index=True)
    evidence_reference = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False)
    vendor_id = Column(String(36), nullable=True)
    service_name = Column(String(255), nullable=False)
    plan_name = Column(String(100), nullable=False)
    amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    billing_interval = Column(String(50), nullable=False, default="MONTHLY")
    renewal_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    status = Column(String(50), nullable=False, default="ACTIVE")
    cancellation_date = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    order_number = Column(String(100), nullable=False)
    customer_id = Column(String(36), nullable=False)
    description = Column(Text, nullable=False)
    total_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="CREATED")
    fulfillment_reference = Column(String(255), nullable=True)
    invoice_id = Column(String(36), nullable=True)
    payment_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class CustomerAccountModel(Base):
    __tablename__ = "customer_accounts"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    external_reference = Column(String(255), nullable=True)
    credit_limit_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class VendorModel(Base):
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    external_reference = Column(String(255), nullable=True)
    categories_json = Column(JSON, nullable=True)
    payment_terms = Column(String(50), nullable=False, default="NET_30")
    status = Column(String(50), nullable=False, default="ACTIVE")
    risk_level = Column(String(50), nullable=False, default="LOW")
    bank_details_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class ProcurementRequestModel(Base):
    __tablename__ = "procurement_requests"

    id = Column(String(36), primary_key=True)
    requester_id = Column(String(36), nullable=False)
    department_id = Column(String(36), nullable=True)
    vendor_id = Column(String(36), nullable=True)
    item_description = Column(Text, nullable=False)
    estimated_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="REQUESTED")
    approval_governance_id = Column(String(36), nullable=True)
    approver_id = Column(String(36), nullable=True)
    purchase_order_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class PurchaseOrderModel(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True)
    po_number = Column(String(100), nullable=False)
    procurement_request_id = Column(String(36), nullable=False)
    vendor_id = Column(String(36), nullable=False)
    requester_id = Column(String(36), nullable=False)
    department_id = Column(String(36), nullable=True)
    total_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="ISSUED")
    approved_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(JSON, nullable=True)


class BudgetModel(Base):
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    company_id = Column(String(36), nullable=False, default="DEFAULT")
    department_id = Column(String(36), nullable=True)
    project_id = Column(String(36), nullable=True)
    period_name = Column(String(50), nullable=False, default="Q3-2026")
    currency = Column(String(10), nullable=False, default="USD")
    allocated_cents = Column(BigInteger, nullable=False, default=0)
    consumed_cents = Column(BigInteger, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class BudgetAllocationModel(Base):
    __tablename__ = "budget_allocations"

    id = Column(String(36), primary_key=True)
    budget_id = Column(String(36), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    allocated_cents = Column(BigInteger, nullable=False, default=0)
    consumed_cents = Column(BigInteger, nullable=False, default=0)
    department_id = Column(String(36), nullable=True)
    project_id = Column(String(36), nullable=True)


class FinancialPeriodModel(Base):
    __tablename__ = "financial_periods"

    id = Column(String(36), primary_key=True)
    period_name = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(50), nullable=False, default="OPEN")
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String(36), nullable=True)


class ReconciliationModel(Base):
    __tablename__ = "reconciliations"

    id = Column(String(36), primary_key=True)
    period_id = Column(String(36), nullable=True)
    source_provider = Column(String(100), nullable=False, default="EXTERNAL_BANK")
    status = Column(String(50), nullable=False, default="PENDING")
    total_matched_cents = Column(BigInteger, nullable=False, default=0)
    total_mismatched_cents = Column(BigInteger, nullable=False, default=0)
    conducted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ReconciliationItemModel(Base):
    __tablename__ = "reconciliation_items"

    id = Column(String(36), primary_key=True)
    reconciliation_id = Column(String(36), nullable=False, index=True)
    internal_ref = Column(String(255), nullable=False)
    external_ref = Column(String(255), nullable=False)
    internal_amount_cents = Column(BigInteger, nullable=False, default=0)
    external_amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="PENDING")
    discrepancy_cents = Column(BigInteger, nullable=False, default=0)
    resolution_notes = Column(Text, nullable=True)


class CashFlowSnapshotModel(Base):
    __tablename__ = "cash_flow_snapshots"

    id = Column(String(36), primary_key=True)
    snapshot_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    currency = Column(String(10), nullable=False, default="USD")
    actual_inflow_cents = Column(BigInteger, nullable=False, default=0)
    actual_outflow_cents = Column(BigInteger, nullable=False, default=0)
    expected_inflow_cents = Column(BigInteger, nullable=False, default=0)
    expected_outflow_cents = Column(BigInteger, nullable=False, default=0)
    committed_spending_cents = Column(BigInteger, nullable=False, default=0)
    available_budget_cents = Column(BigInteger, nullable=False, default=0)


class BusinessMetricModel(Base):
    __tablename__ = "business_metrics"

    id = Column(String(36), primary_key=True)
    metric_name = Column(String(100), nullable=False, index=True)
    value_cents = Column(BigInteger, nullable=True)
    numeric_value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=False, default="USD")
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    provenance_references_json = Column(JSON, nullable=True)


class BusinessProcessModel(Base):
    __tablename__ = "business_processes"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    process_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="DEFINED")
    associated_task_ids_json = Column(JSON, nullable=True)
    step_history_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
