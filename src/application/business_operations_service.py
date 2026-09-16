"""
Central Application Service Facade for Phase 23 Business Operations & Financial Operations.

Orchestrates business transactions, invoices, expenses, revenue, payments, procurement,
budgets, reconciliations, cash-flow snapshots, metrics, and business processes.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.business import (
    BusinessAccount,
    BusinessTransaction,
    RevenueRecord,
    ExpenseRecord,
    Invoice,
    InvoiceLine,
    Payment,
    Subscription,
    ProcurementRequest,
    PurchaseOrder,
    Budget,
    FinancialPeriod,
    Reconciliation,
    ReconciliationItem,
    CashFlowSnapshot,
    BusinessMetric,
    BusinessProcess,
    Money,
    AccountType,
    TransactionType,
    TransactionStatus,
    RevenueRecognitionState,
    ExpenseApprovalState,
    InvoiceStatus,
    PaymentStatus,
    ProcurementStatus,
    ReconciliationStatus,
    FinancialPeriodState,
    BusinessProcessStatus,
)
from src.domain.events import (
    BusinessTransactionRecordedEvent,
    RevenueRecordedEvent,
    ExpenseRecordedEvent,
    InvoiceCreatedEvent,
    InvoiceIssuedEvent,
    PaymentRecordedEvent,
    ProcurementRequestedEvent,
    ProcurementApprovedEvent,
    PurchaseOrderCreatedEvent,
    BudgetExceededEvent,
    ReconciliationMismatchEvent,
    ReconciliationCompletedEvent,
)
from src.domain.exceptions import (
    IdempotencyConflictError,
    BudgetExceededError,
    UnauthorizedFinancialActionError,
    ReconciliationMismatchError,
)
from src.domain.repository import BusinessRepositoryInterface
from src.application.reconciliation_engine import ReconciliationEngine
from src.application.procurement_workflow_engine import ProcurementWorkflowEngine
from src.application.budget_control_engine import BudgetControlEngine
from src.application.business_governance_service import BusinessGovernanceService
from src.application.business_observability_service import BusinessObservabilityService


class BusinessOperationsService:
    """Core orchestration service for Business & Financial Operations."""

    def __init__(
        self,
        repository: BusinessRepositoryInterface,
        outbox_publisher: Optional[Any] = None,
        governance_service: Optional[BusinessGovernanceService] = None,
        observability_service: Optional[BusinessObservabilityService] = None,
    ) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher
        self.governance = governance_service or BusinessGovernanceService()
        self.observability = observability_service or BusinessObservabilityService()
        self.reconciliation_engine = ReconciliationEngine()
        self.procurement_engine = ProcurementWorkflowEngine()
        self.budget_engine = BudgetControlEngine()

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    # --- Transactions ---
    async def record_transaction(
        self,
        transaction_type: TransactionType,
        amount_cents: int,
        currency: str,
        account_id: str,
        counterparty: str,
        source: str = "INTERNAL",
        external_reference: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        evidence_reference: Optional[str] = None,
        actor_id: str = "SYSTEM",
    ) -> BusinessTransaction:
        # Check idempotency
        if idempotency_key:
            existing = await self.repository.get_transaction_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        # Validate Money object
        m = Money(amount_cents, currency)

        tx = BusinessTransaction(
            id=str(uuid.uuid4()),
            transaction_type=transaction_type,
            amount_cents=m.amount_cents,
            currency=m.currency,
            account_id=account_id,
            counterparty=counterparty,
            source=source,
            external_reference=external_reference,
            status=TransactionStatus.VERIFIED,
            occurred_at=datetime.now(UTC),
            recorded_at=datetime.now(UTC),
            evidence_reference=evidence_reference,
            verification_status="VERIFIED",
            reconciliation_status=ReconciliationStatus.PENDING,
            idempotency_key=idempotency_key,
        )

        saved = await self.repository.save_transaction(tx)

        self._publish_event(
            BusinessTransactionRecordedEvent(
                transaction_id=saved.id,
                transaction_type=saved.transaction_type.value,
                amount_cents=saved.amount_cents,
                currency=saved.currency,
                account_id=saved.account_id,
                counterparty=saved.counterparty,
                idempotency_key=saved.idempotency_key,
            )
        )

        self.observability.log_financial_action(
            action="RECORD_TRANSACTION",
            actor_id=actor_id,
            amount_cents=saved.amount_cents,
            currency=saved.currency,
            evidence_reference=evidence_reference,
        )

        return saved

    # --- Revenue & Expenses ---
    async def record_revenue(
        self,
        source: str,
        customer_id: str,
        product_service: str,
        amount_cents: int,
        currency: str = "USD",
        invoice_id: Optional[str] = None,
        actor_id: str = "SYSTEM",
    ) -> RevenueRecord:
        m = Money(amount_cents, currency)
        rev = RevenueRecord(
            id=str(uuid.uuid4()),
            source=source,
            customer_id=customer_id,
            product_service=product_service,
            amount_cents=m.amount_cents,
            currency=m.currency,
            invoice_id=invoice_id,
            recognition_state=RevenueRecognitionState.INVOICED if invoice_id else RevenueRecognitionState.EXPECTED,
            verification_status="VERIFIED",
            recorded_at=datetime.now(UTC),
        )
        saved = await self.repository.save_revenue(rev)
        self._publish_event(
            RevenueRecordedEvent(
                revenue_id=saved.id,
                customer_id=saved.customer_id,
                amount_cents=saved.amount_cents,
                currency=saved.currency,
                recognition_state=saved.recognition_state.value,
            )
        )
        self.observability.log_financial_action("RECORD_REVENUE", actor_id, saved.amount_cents, saved.currency)
        return saved

    async def record_expense(
        self,
        vendor_id: str,
        category: str,
        amount_cents: int,
        currency: str = "USD",
        department_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        actor_id: str = "SYSTEM",
    ) -> ExpenseRecord:
        m = Money(amount_cents, currency)
        exp = ExpenseRecord(
            id=str(uuid.uuid4()),
            vendor_id=vendor_id,
            category=category,
            amount_cents=m.amount_cents,
            currency=m.currency,
            department_id=department_id,
            purchase_order_id=purchase_order_id,
            approval_state=ExpenseApprovalState.RECORDED,
            verification_status="VERIFIED",
            incurred_date=datetime.now(UTC),
        )
        saved = await self.repository.save_expense(exp)
        self._publish_event(
            ExpenseRecordedEvent(
                expense_id=saved.id,
                vendor_id=saved.vendor_id,
                category=saved.category,
                amount_cents=saved.amount_cents,
                currency=saved.currency,
                department_id=saved.department_id,
            )
        )
        self.observability.log_financial_action("RECORD_EXPENSE", actor_id, saved.amount_cents, saved.currency)
        return saved

    # --- Invoices ---
    async def create_invoice(
        self,
        customer_id: str,
        lines: List[Dict[str, Any]],
        tax_cents: int = 0,
        currency: str = "USD",
        idempotency_key: Optional[str] = None,
        actor_id: str = "SYSTEM",
    ) -> Invoice:
        line_items: List[InvoiceLine] = []
        for idx, l in enumerate(lines):
            line = InvoiceLine(
                id=str(uuid.uuid4()),
                description=l.get("description", f"Line {idx+1}"),
                quantity=int(l.get("quantity", 1)),
                unit_price_cents=int(l.get("unit_price_cents", 0)),
            )
            line.calculate_subtotal()
            line_items.append(line)

        inv_num = f"INV-{datetime.now(UTC).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        invoice = Invoice(
            id=str(uuid.uuid4()),
            invoice_number=inv_num,
            customer_id=customer_id,
            line_items=line_items,
            tax_cents=tax_cents,
            currency=currency,
            issue_date=datetime.now(UTC),
            due_date=datetime.now(UTC),
            status=InvoiceStatus.DRAFT,
            idempotency_key=idempotency_key,
        )
        invoice.recalculate_totals()

        saved = await self.repository.save_invoice(invoice)
        self._publish_event(
            InvoiceCreatedEvent(
                invoice_id=saved.id,
                invoice_number=saved.invoice_number,
                customer_id=saved.customer_id,
                total_cents=saved.total_cents,
                currency=saved.currency,
                status=saved.status.value,
            )
        )
        self.observability.log_financial_action("CREATE_INVOICE_DRAFT", actor_id, saved.total_cents, saved.currency)
        return saved

    async def issue_and_send_invoice(
        self,
        invoice_id: str,
        actor_id: str,
        governance_approval_id: Optional[str] = None,
    ) -> Invoice:
        inv = await self.repository.get_invoice_by_id(invoice_id)
        if not inv:
            raise ValueError(f"Invoice '{invoice_id}' not found.")

        # Evaluate governance & approval requirement for sending invoice
        self.governance.evaluate_and_authorize(
            action_type="SEND_INVOICE",
            actor_id=actor_id,
            amount_cents=inv.total_cents,
            currency=inv.currency,
            approval_id=governance_approval_id,
        )

        inv.status = InvoiceStatus.SENT
        inv.governance_approval_id = governance_approval_id
        saved = await self.repository.save_invoice(inv)

        self._publish_event(
            InvoiceIssuedEvent(
                invoice_id=saved.id,
                invoice_number=saved.invoice_number,
                issued_by=actor_id,
            )
        )
        self.observability.log_financial_action("SEND_INVOICE", actor_id, saved.total_cents, saved.currency)
        return saved

    # --- Payments ---
    async def record_payment(
        self,
        counterparty: str,
        amount_cents: int,
        currency: str = "USD",
        invoice_id: Optional[str] = None,
        external_reference: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        governance_approval_id: Optional[str] = None,
        actor_id: str = "SYSTEM",
    ) -> Payment:
        if idempotency_key:
            existing = await self.repository.get_payment_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        # Payment execution requires governance evaluation
        self.governance.evaluate_and_authorize(
            action_type="SUBMIT_PAYMENT",
            actor_id=actor_id,
            amount_cents=amount_cents,
            currency=currency,
            approval_id=governance_approval_id,
        )

        p = Payment(
            id=str(uuid.uuid4()),
            invoice_id=invoice_id,
            amount_cents=amount_cents,
            currency=currency,
            counterparty=counterparty,
            external_reference=external_reference,
            status=PaymentStatus.CONFIRMED,
            initiated_at=datetime.now(UTC),
            confirmed_at=datetime.now(UTC),
            governance_approval_id=governance_approval_id,
            idempotency_key=idempotency_key,
        )

        saved = await self.repository.save_payment(p)

        # Update invoice status if linked
        if invoice_id:
            inv = await self.repository.get_invoice_by_id(invoice_id)
            if inv:
                inv.status = InvoiceStatus.PAID
                inv.payment_reference = saved.id
                await self.repository.save_invoice(inv)

        self._publish_event(
            PaymentRecordedEvent(
                payment_id=saved.id,
                invoice_id=saved.invoice_id,
                amount_cents=saved.amount_cents,
                currency=saved.currency,
                status=saved.status.value,
            )
        )
        self.observability.log_financial_action("RECORD_PAYMENT", actor_id, saved.amount_cents, saved.currency)
        return saved

    # --- Procurement ---
    async def request_procurement(
        self,
        requester_id: str,
        item_description: str,
        estimated_cents: int,
        currency: str = "USD",
        department_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
    ) -> ProcurementRequest:
        req = self.procurement_engine.create_request(
            requester_id=requester_id,
            item_description=item_description,
            estimated_cents=estimated_cents,
            currency=currency,
            department_id=department_id,
            vendor_id=vendor_id,
        )
        saved = await self.repository.save_procurement(req)
        self._publish_event(
            ProcurementRequestedEvent(
                request_id=saved.id,
                requester_id=saved.requester_id,
                item_description=saved.item_description,
                estimated_cents=saved.estimated_cents,
                currency=saved.currency,
            )
        )
        return saved

    async def approve_procurement_and_issue_po(
        self,
        request_id: str,
        approver_id: str,
        vendor_id: str,
        budget_id: Optional[str] = None,
        governance_approval_id: Optional[str] = None,
    ) -> PurchaseOrder:
        req = await self.repository.get_procurement_by_id(request_id)
        if not req:
            raise ValueError(f"ProcurementRequest '{request_id}' not found.")

        # Governance evaluation
        self.governance.evaluate_and_authorize(
            action_type="APPROVE_PROCUREMENT",
            actor_id=approver_id,
            amount_cents=req.estimated_cents,
            currency=req.currency,
            approval_id=governance_approval_id,
        )

        # Approve in workflow engine (enforces Separation of Duties: Requester != Approver)
        self.procurement_engine.approve_request(req, approver_id, governance_approval_id)

        # Budget Check if budget provided
        if budget_id:
            budget = await self.repository.get_budget_by_id(budget_id)
            if budget:
                self.budget_engine.check_and_consume(budget, req.estimated_cents)
                await self.repository.save_budget(budget)

        po_num = f"PO-{datetime.now(UTC).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        po = self.procurement_engine.generate_purchase_order(req, po_num, vendor_id, approver_id)

        await self.repository.save_procurement(req)

        self._publish_event(
            ProcurementApprovedEvent(
                request_id=req.id,
                approved_by=approver_id,
                purchase_order_id=po.id,
            )
        )
        self._publish_event(
            PurchaseOrderCreatedEvent(
                purchase_order_id=po.id,
                vendor_id=po.vendor_id,
                total_cents=po.total_cents,
            )
        )
        self.observability.log_financial_action("APPROVE_PROCUREMENT", approver_id, req.estimated_cents, req.currency)
        return po

    # --- Reconciliation ---
    async def run_reconciliation(
        self,
        external_statements: List[Dict[str, Any]],
        source_provider: str = "EXTERNAL_BANK",
    ) -> Reconciliation:
        txs = await self.repository.list_transactions()
        rec = self.reconciliation_engine.reconcile_records(txs, external_statements, source_provider)
        saved = await self.repository.save_reconciliation(rec)

        if saved.status == ReconciliationStatus.MISMATCH:
            self._publish_event(
                ReconciliationMismatchEvent(
                    reconciliation_id=saved.id,
                    internal_ref="BATCH_RECON",
                    external_ref=source_provider,
                    internal_cents=saved.total_matched_cents + saved.total_mismatched_cents,
                    external_cents=saved.total_matched_cents,
                )
            )
        else:
            self._publish_event(
                ReconciliationCompletedEvent(
                    reconciliation_id=saved.id,
                    status=saved.status.value,
                    matched_count=len([i for i in saved.items if i.status == ReconciliationStatus.MATCHED]),
                    mismatch_count=len([i for i in saved.items if i.status == ReconciliationStatus.MISMATCH]),
                )
            )

        return saved

    # --- Cash Flow & Reporting ---
    async def get_cash_flow_snapshot(self) -> CashFlowSnapshot:
        latest = await self.repository.get_latest_cash_flow()
        if latest:
            return latest

        revs = await self.repository.list_revenues()
        exps = await self.repository.list_expenses()
        budgets = await self.repository.list_budgets()

        actual_inflow = sum(r.amount_cents for r in revs if r.recognition_state in (RevenueRecognitionState.RECEIVED, RevenueRecognitionState.VERIFIED))
        expected_inflow = sum(r.amount_cents for r in revs if r.recognition_state in (RevenueRecognitionState.EXPECTED, RevenueRecognitionState.INVOICED))

        actual_outflow = sum(e.amount_cents for e in exps if e.approval_state in (ExpenseApprovalState.RECORDED, ExpenseApprovalState.VERIFIED, ExpenseApprovalState.RECONCILED))
        expected_outflow = sum(e.amount_cents for e in exps if e.approval_state in (ExpenseApprovalState.REQUESTED, ExpenseApprovalState.APPROVED))

        avail_budget = sum(b.remaining_cents for b in budgets)

        snapshot = CashFlowSnapshot(
            id=str(uuid.uuid4()),
            snapshot_date=datetime.now(UTC),
            currency="USD",
            actual_inflow_cents=actual_inflow,
            actual_outflow_cents=actual_outflow,
            expected_inflow_cents=expected_inflow,
            expected_outflow_cents=expected_outflow,
            committed_spending_cents=expected_outflow,
            available_budget_cents=avail_budget,
        )
        return await self.repository.save_cash_flow(snapshot)
