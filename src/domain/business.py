"""
Business Operations & Financial Domain Models for Autonomous AI Organization Platform (Phase 23).

Defines core business entities, deterministic money representation, value objects,
financial lifecycles, and governance invariants.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from src.domain.exceptions import MoneyArithmeticError, BudgetExceededError, FinancialPeriodClosedError, ReconciliationMismatchError


class AccountType(str, Enum):
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
    OPERATING = "OPERATING"
    RECEIVABLE = "RECEIVABLE"
    PAYABLE = "PAYABLE"
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    BUDGET = "BUDGET"
    INTERNAL = "INTERNAL"


class TransactionType(str, Enum):
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
    REFUND = "REFUND"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    TRANSFER = "TRANSFER"
    PURCHASE = "PURCHASE"
    SUBSCRIPTION = "SUBSCRIPTION"
    FEE = "FEE"
    CREDIT = "CREDIT"
    ADJUSTMENT = "ADJUSTMENT"


class TransactionStatus(str, Enum):
    RECORDED = "RECORDED"
    VALIDATING = "VALIDATING"
    VERIFIED = "VERIFIED"
    RECONCILED = "RECONCILED"
    INVALID = "INVALID"
    DISPUTED = "DISPUTED"
    UNRECONCILED = "UNRECONCILED"
    CANCELLED = "CANCELLED"


class RevenueRecognitionState(str, Enum):
    EXPECTED = "EXPECTED"
    INVOICED = "INVOICED"
    RECEIVED = "RECEIVED"
    VERIFIED = "VERIFIED"


class ExpenseApprovalState(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    INCURRED = "INCURRED"
    RECORDED = "RECORDED"
    VERIFIED = "VERIFIED"
    RECONCILED = "RECONCILED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    SENT = "SENT"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    VOID = "VOID"
    OVERDUE = "OVERDUE"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    EXPECTED = "EXPECTED"
    INITIATED = "INITIATED"
    SUBMITTED = "SUBMITTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    RECONCILED = "RECONCILED"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    PENDING_RENEWAL = "PENDING_RENEWAL"


class ProcurementStatus(str, Enum):
    REQUESTED = "REQUESTED"
    REVIEW = "REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    RECEIVED = "RECEIVED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


class ReconciliationStatus(str, Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISMATCH = "MISMATCH"
    DISPUTED = "DISPUTED"
    RESOLVED = "RESOLVED"


class FinancialPeriodState(str, Enum):
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    REOPENED_WITH_AUTHORIZATION = "REOPENED_WITH_AUTHORIZATION"


class BusinessProcessStatus(str, Enum):
    DEFINED = "DEFINED"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Money:
    """
    Deterministic monetary value representation.
    Never uses float arithmetic directly to prevent IEEE 754 precision loss.
    """
    amount_cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not isinstance(self.amount_cents, int):
            raise MoneyArithmeticError(f"Monetary amount_cents must be an integer, got {type(self.amount_cents).__name__}")
        if not self.currency or len(self.currency) != 3:
            raise MoneyArithmeticError(f"Currency must be a valid 3-character ISO code, got '{self.currency}'")
        object.__setattr__(self, "currency", self.currency.upper())

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise MoneyArithmeticError(f"Cannot add mismatched currencies: {self.currency} and {other.currency}")
        return Money(self.amount_cents + other.amount_cents, self.currency)

    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise MoneyArithmeticError(f"Cannot subtract mismatched currencies: {self.currency} and {other.currency}")
        return Money(self.amount_cents - other.amount_cents, self.currency)

    def multiply(self, factor: int | float) -> "Money":
        return Money(round(self.amount_cents * factor), self.currency)

    def to_dollars(self) -> float:
        return self.amount_cents / 100.0

    @classmethod
    def from_dollars(cls, dollars: float | int, currency: str = "USD") -> "Money":
        return cls(amount_cents=round(dollars * 100), currency=currency)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount_cents": self.amount_cents,
            "dollars": self.to_dollars(),
            "currency": self.currency,
        }


@dataclass
class BusinessAccount:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_code: str = ""
    name: str = ""
    account_type: AccountType = AccountType.OPERATING
    currency: str = "USD"
    balance_cents: int = 0
    department_id: Optional[str] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def money_balance(self) -> Money:
        return Money(self.balance_cents, self.currency)


@dataclass
class BusinessTransaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    transaction_type: TransactionType = TransactionType.EXPENSE
    amount_cents: int = 0
    currency: str = "USD"
    account_id: str = ""
    counterparty: str = ""
    source: str = "INTERNAL"
    external_reference: Optional[str] = None
    status: TransactionStatus = TransactionStatus.RECORDED
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    evidence_reference: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def money_amount(self) -> Money:
        return Money(self.amount_cents, self.currency)


@dataclass
class RevenueRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    customer_id: str = ""
    product_service: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    period_id: Optional[str] = None
    invoice_id: Optional[str] = None
    recognition_state: RevenueRecognitionState = RevenueRecognitionState.EXPECTED
    evidence_reference: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def money_amount(self) -> Money:
        return Money(self.amount_cents, self.currency)


@dataclass
class ExpenseRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str = ""
    category: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    incurred_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    project_id: Optional[str] = None
    department_id: Optional[str] = None
    employee_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    approval_state: ExpenseApprovalState = ExpenseApprovalState.REQUESTED
    evidence_reference: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def money_amount(self) -> Money:
        return Money(self.amount_cents, self.currency)


@dataclass
class InvoiceLine:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    quantity: int = 1
    unit_price_cents: int = 0
    subtotal_cents: int = 0

    def calculate_subtotal(self) -> int:
        self.subtotal_cents = self.quantity * self.unit_price_cents
        return self.subtotal_cents


@dataclass
class Invoice:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_number: str = ""
    customer_id: str = ""
    issuer_name: str = "Autonomous AI Corp"
    line_items: List[InvoiceLine] = field(default_factory=list)
    subtotal_cents: int = 0
    tax_cents: int = 0
    total_cents: int = 0
    currency: str = "USD"
    issue_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    due_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: InvoiceStatus = InvoiceStatus.DRAFT
    evidence_reference: Optional[str] = None
    payment_reference: Optional[str] = None
    governance_approval_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def recalculate_totals(self) -> None:
        self.subtotal_cents = sum(line.calculate_subtotal() for line in self.line_items)
        self.total_cents = self.subtotal_cents + self.tax_cents


@dataclass
class Payment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: Optional[str] = None
    amount_cents: int = 0
    currency: str = "USD"
    payment_method: str = "BANK_TRANSFER"
    counterparty: str = ""
    external_reference: Optional[str] = None
    status: PaymentStatus = PaymentStatus.EXPECTED
    initiated_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    governance_approval_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    evidence_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    vendor_id: Optional[str] = None
    service_name: str = ""
    plan_name: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    billing_interval: str = "MONTHLY"
    renewal_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    cancellation_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Order:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = ""
    customer_id: str = ""
    description: str = ""
    total_cents: int = 0
    currency: str = "USD"
    status: str = "CREATED"
    fulfillment_reference: Optional[str] = None
    invoice_id: Optional[str] = None
    payment_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerAccount:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    external_reference: Optional[str] = None
    credit_limit_cents: int = 0
    currency: str = "USD"
    status: str = "ACTIVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Vendor:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    external_reference: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    payment_terms: str = "NET_30"
    status: str = "ACTIVE"
    risk_level: str = "LOW"
    bank_details_verified: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcurementRequest:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requester_id: str = ""
    department_id: Optional[str] = None
    vendor_id: Optional[str] = None
    item_description: str = ""
    estimated_cents: int = 0
    currency: str = "USD"
    status: ProcurementStatus = ProcurementStatus.REQUESTED
    approval_governance_id: Optional[str] = None
    approver_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PurchaseOrder:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    po_number: str = ""
    procurement_request_id: str = ""
    vendor_id: str = ""
    requester_id: str = ""
    department_id: Optional[str] = None
    total_cents: int = 0
    currency: str = "USD"
    status: str = "ISSUED"
    approved_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetAllocation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""
    allocated_cents: int = 0
    consumed_cents: int = 0
    department_id: Optional[str] = None
    project_id: Optional[str] = None

    @property
    def remaining_cents(self) -> int:
        return max(0, self.allocated_cents - self.consumed_cents)


@dataclass
class Budget:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    company_id: str = "DEFAULT"
    department_id: Optional[str] = None
    project_id: Optional[str] = None
    period_name: str = "Q3-2026"
    currency: str = "USD"
    allocated_cents: int = 0
    consumed_cents: int = 0
    status: str = "ACTIVE"
    allocations: List[BudgetAllocation] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def remaining_cents(self) -> int:
        return self.allocated_cents - self.consumed_cents

    def consume(self, amount_cents: int) -> None:
        if amount_cents > self.remaining_cents:
            raise BudgetExceededError(self.id, amount_cents, self.remaining_cents)
        self.consumed_cents += amount_cents


@dataclass
class FinancialPeriod:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    period_name: str = ""
    start_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    state: FinancialPeriodState = FinancialPeriodState.OPEN
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None

    def ensure_open(self) -> None:
        if self.state == FinancialPeriodState.CLOSED:
            raise FinancialPeriodClosedError(self.id)


@dataclass
class ReconciliationItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    internal_ref: str = ""
    external_ref: str = ""
    internal_amount_cents: int = 0
    external_amount_cents: int = 0
    currency: str = "USD"
    status: ReconciliationStatus = ReconciliationStatus.PENDING
    discrepancy_cents: int = 0
    resolution_notes: Optional[str] = None


@dataclass
class Reconciliation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    period_id: Optional[str] = None
    source_provider: str = "EXTERNAL_BANK"
    status: ReconciliationStatus = ReconciliationStatus.PENDING
    items: List[ReconciliationItem] = field(default_factory=list)
    total_matched_cents: int = 0
    total_mismatched_cents: int = 0
    conducted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CashFlowSnapshot:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    snapshot_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    currency: str = "USD"
    actual_inflow_cents: int = 0
    actual_outflow_cents: int = 0
    expected_inflow_cents: int = 0
    expected_outflow_cents: int = 0
    committed_spending_cents: int = 0
    available_budget_cents: int = 0

    @property
    def net_actual_cash_cents(self) -> int:
        return self.actual_inflow_cents - self.actual_outflow_cents


@dataclass
class BusinessMetric:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    value_cents: Optional[int] = None
    numeric_value: Optional[float] = None
    unit: str = "USD"
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    provenance_references: List[str] = field(default_factory=list)


@dataclass
class BusinessProcess:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    process_type: str = ""
    status: BusinessProcessStatus = BusinessProcessStatus.DEFINED
    associated_task_ids: List[str] = field(default_factory=list)
    step_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
