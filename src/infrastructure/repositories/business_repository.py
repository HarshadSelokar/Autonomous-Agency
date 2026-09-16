"""
SQLAlchemy Async Repository implementation for Phase 23 Business & Financial Operations.
"""

from collections.abc import Sequence
from typing import Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.repository import BusinessRepositoryInterface
from src.domain.business import (
    BusinessAccount,
    BusinessTransaction,
    RevenueRecord,
    ExpenseRecord,
    Invoice,
    InvoiceLine,
    Payment,
    Subscription,
    Order,
    CustomerAccount,
    Vendor,
    ProcurementRequest,
    PurchaseOrder,
    Budget,
    BudgetAllocation,
    FinancialPeriod,
    Reconciliation,
    ReconciliationItem,
    CashFlowSnapshot,
    BusinessMetric,
    BusinessProcess,
    AccountType,
    TransactionType,
    TransactionStatus,
    RevenueRecognitionState,
    ExpenseApprovalState,
    InvoiceStatus,
    PaymentStatus,
    SubscriptionStatus,
    ProcurementStatus,
    ReconciliationStatus,
    FinancialPeriodState,
    BusinessProcessStatus,
)
from src.infrastructure.models.business_model import (
    BusinessAccountModel,
    BusinessTransactionModel,
    RevenueRecordModel,
    ExpenseRecordModel,
    InvoiceModel,
    InvoiceLineModel,
    PaymentModel,
    SubscriptionModel,
    OrderModel,
    CustomerAccountModel,
    VendorModel,
    ProcurementRequestModel,
    PurchaseOrderModel,
    BudgetModel,
    BudgetAllocationModel,
    FinancialPeriodModel,
    ReconciliationModel,
    ReconciliationItemModel,
    CashFlowSnapshotModel,
    BusinessMetricModel,
    BusinessProcessModel,
)


class SQLAlchemyBusinessRepository(BusinessRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Business Account ---
    async def save_account(self, account: BusinessAccount) -> BusinessAccount:
        stmt = select(BusinessAccountModel).where(BusinessAccountModel.id == account.id)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()

        if model is None:
            model = BusinessAccountModel(
                id=account.id,
                account_code=account.account_code,
                name=account.name,
                account_type=account.account_type.value if hasattr(account.account_type, "value") else str(account.account_type),
                currency=account.currency,
                balance_cents=account.balance_cents,
                department_id=account.department_id,
                is_active=account.is_active,
                metadata_json=account.metadata,
                created_at=account.created_at,
            )
            self.session.add(model)
        else:
            model.balance_cents = account.balance_cents
            model.is_active = account.is_active
            model.metadata_json = account.metadata

        await self.session.commit()
        return account

    async def get_account_by_id(self, account_id: str) -> Optional[BusinessAccount]:
        stmt = select(BusinessAccountModel).where(BusinessAccountModel.id == account_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return BusinessAccount(
            id=m.id,
            account_code=m.account_code,
            name=m.name,
            account_type=AccountType(m.account_type),
            currency=m.currency,
            balance_cents=m.balance_cents,
            department_id=m.department_id,
            is_active=m.is_active,
            metadata=m.metadata_json or {},
            created_at=m.created_at,
        )

    async def list_accounts(self) -> List[BusinessAccount]:
        stmt = select(BusinessAccountModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            BusinessAccount(
                id=m.id,
                account_code=m.account_code,
                name=m.name,
                account_type=AccountType(m.account_type),
                currency=m.currency,
                balance_cents=m.balance_cents,
                department_id=m.department_id,
                is_active=m.is_active,
                metadata=m.metadata_json or {},
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Transactions ---
    async def save_transaction(self, tx: BusinessTransaction) -> BusinessTransaction:
        stmt = select(BusinessTransactionModel).where(BusinessTransactionModel.id == tx.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = BusinessTransactionModel(
                id=tx.id,
                transaction_type=tx.transaction_type.value if hasattr(tx.transaction_type, "value") else str(tx.transaction_type),
                amount_cents=tx.amount_cents,
                currency=tx.currency,
                account_id=tx.account_id,
                counterparty=tx.counterparty,
                source=tx.source,
                external_reference=tx.external_reference,
                status=tx.status.value if hasattr(tx.status, "value") else str(tx.status),
                occurred_at=tx.occurred_at,
                recorded_at=tx.recorded_at,
                evidence_reference=tx.evidence_reference,
                verification_status=tx.verification_status,
                reconciliation_status=tx.reconciliation_status.value if hasattr(tx.reconciliation_status, "value") else str(tx.reconciliation_status),
                idempotency_key=tx.idempotency_key,
                metadata_json=tx.metadata,
            )
            self.session.add(m)
        else:
            m.status = tx.status.value if hasattr(tx.status, "value") else str(tx.status)
            m.verification_status = tx.verification_status
            m.reconciliation_status = tx.reconciliation_status.value if hasattr(tx.reconciliation_status, "value") else str(tx.reconciliation_status)
            m.evidence_reference = tx.evidence_reference
            m.metadata_json = tx.metadata

        await self.session.commit()
        return tx

    async def get_transaction_by_id(self, tx_id: str) -> Optional[BusinessTransaction]:
        stmt = select(BusinessTransactionModel).where(BusinessTransactionModel.id == tx_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return BusinessTransaction(
            id=m.id,
            transaction_type=TransactionType(m.transaction_type),
            amount_cents=m.amount_cents,
            currency=m.currency,
            account_id=m.account_id,
            counterparty=m.counterparty,
            source=m.source,
            external_reference=m.external_reference,
            status=TransactionStatus(m.status),
            occurred_at=m.occurred_at,
            recorded_at=m.recorded_at,
            evidence_reference=m.evidence_reference,
            verification_status=m.verification_status,
            reconciliation_status=ReconciliationStatus(m.reconciliation_status),
            idempotency_key=m.idempotency_key,
            metadata=m.metadata_json or {},
        )

    async def get_transaction_by_idempotency_key(self, key: str) -> Optional[BusinessTransaction]:
        stmt = select(BusinessTransactionModel).where(BusinessTransactionModel.idempotency_key == key)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return BusinessTransaction(
            id=m.id,
            transaction_type=TransactionType(m.transaction_type),
            amount_cents=m.amount_cents,
            currency=m.currency,
            account_id=m.account_id,
            counterparty=m.counterparty,
            source=m.source,
            external_reference=m.external_reference,
            status=TransactionStatus(m.status),
            occurred_at=m.occurred_at,
            recorded_at=m.recorded_at,
            evidence_reference=m.evidence_reference,
            verification_status=m.verification_status,
            reconciliation_status=ReconciliationStatus(m.reconciliation_status),
            idempotency_key=m.idempotency_key,
            metadata=m.metadata_json or {},
        )

    async def list_transactions(self) -> List[BusinessTransaction]:
        stmt = select(BusinessTransactionModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            BusinessTransaction(
                id=m.id,
                transaction_type=TransactionType(m.transaction_type),
                amount_cents=m.amount_cents,
                currency=m.currency,
                account_id=m.account_id,
                counterparty=m.counterparty,
                source=m.source,
                external_reference=m.external_reference,
                status=TransactionStatus(m.status),
                occurred_at=m.occurred_at,
                recorded_at=m.recorded_at,
                evidence_reference=m.evidence_reference,
                verification_status=m.verification_status,
                reconciliation_status=ReconciliationStatus(m.reconciliation_status),
                idempotency_key=m.idempotency_key,
                metadata=m.metadata_json or {},
            )
            for m in models
        ]

    # --- Invoices ---
    async def save_invoice(self, invoice: Invoice) -> Invoice:
        stmt = select(InvoiceModel).where(InvoiceModel.id == invoice.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = InvoiceModel(
                id=invoice.id,
                invoice_number=invoice.invoice_number,
                customer_id=invoice.customer_id,
                issuer_name=invoice.issuer_name,
                subtotal_cents=invoice.subtotal_cents,
                tax_cents=invoice.tax_cents,
                total_cents=invoice.total_cents,
                currency=invoice.currency,
                issue_date=invoice.issue_date,
                due_date=invoice.due_date,
                status=invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status),
                evidence_reference=invoice.evidence_reference,
                payment_reference=invoice.payment_reference,
                governance_approval_id=invoice.governance_approval_id,
                idempotency_key=invoice.idempotency_key,
                metadata_json=invoice.metadata,
            )
            self.session.add(m)
        else:
            m.status = invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status)
            m.subtotal_cents = invoice.subtotal_cents
            m.total_cents = invoice.total_cents
            m.evidence_reference = invoice.evidence_reference
            m.payment_reference = invoice.payment_reference
            m.governance_approval_id = invoice.governance_approval_id
            m.metadata_json = invoice.metadata

        # Save invoice lines
        for line in invoice.line_items:
            line_stmt = select(InvoiceLineModel).where(InvoiceLineModel.id == line.id)
            line_res = await self.session.execute(line_stmt)
            lm = line_res.scalar_one_or_none()
            if lm is None:
                lm = InvoiceLineModel(
                    id=line.id,
                    invoice_id=invoice.id,
                    description=line.description,
                    quantity=line.quantity,
                    unit_price_cents=line.unit_price_cents,
                    subtotal_cents=line.subtotal_cents,
                )
                self.session.add(lm)

        await self.session.commit()
        return invoice

    async def get_invoice_by_id(self, invoice_id: str) -> Optional[Invoice]:
        stmt = select(InvoiceModel).where(InvoiceModel.id == invoice_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None

        lines_stmt = select(InvoiceLineModel).where(InvoiceLineModel.invoice_id == invoice_id)
        lines_res = await self.session.execute(lines_stmt)
        line_models = lines_res.scalars().all()

        line_items = [
            InvoiceLine(
                id=lm.id,
                description=lm.description,
                quantity=lm.quantity,
                unit_price_cents=lm.unit_price_cents,
                subtotal_cents=lm.subtotal_cents,
            )
            for lm in line_models
        ]

        return Invoice(
            id=m.id,
            invoice_number=m.invoice_number,
            customer_id=m.customer_id,
            issuer_name=m.issuer_name,
            line_items=line_items,
            subtotal_cents=m.subtotal_cents,
            tax_cents=m.tax_cents,
            total_cents=m.total_cents,
            currency=m.currency,
            issue_date=m.issue_date,
            due_date=m.due_date,
            status=InvoiceStatus(m.status),
            evidence_reference=m.evidence_reference,
            payment_reference=m.payment_reference,
            governance_approval_id=m.governance_approval_id,
            idempotency_key=m.idempotency_key,
            metadata=m.metadata_json or {},
        )

    async def list_invoices(self) -> List[Invoice]:
        stmt = select(InvoiceModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        result = []
        for m in models:
            lines_stmt = select(InvoiceLineModel).where(InvoiceLineModel.invoice_id == m.id)
            lines_res = await self.session.execute(lines_stmt)
            line_models = lines_res.scalars().all()
            line_items = [
                InvoiceLine(
                    id=lm.id,
                    description=lm.description,
                    quantity=lm.quantity,
                    unit_price_cents=lm.unit_price_cents,
                    subtotal_cents=lm.subtotal_cents,
                )
                for lm in line_models
            ]
            result.append(
                Invoice(
                    id=m.id,
                    invoice_number=m.invoice_number,
                    customer_id=m.customer_id,
                    issuer_name=m.issuer_name,
                    line_items=line_items,
                    subtotal_cents=m.subtotal_cents,
                    tax_cents=m.tax_cents,
                    total_cents=m.total_cents,
                    currency=m.currency,
                    issue_date=m.issue_date,
                    due_date=m.due_date,
                    status=InvoiceStatus(m.status),
                    evidence_reference=m.evidence_reference,
                    payment_reference=m.payment_reference,
                    governance_approval_id=m.governance_approval_id,
                    idempotency_key=m.idempotency_key,
                    metadata=m.metadata_json or {},
                )
            )
        return result

    # --- Revenue Records ---
    async def save_revenue(self, rev: RevenueRecord) -> RevenueRecord:
        stmt = select(RevenueRecordModel).where(RevenueRecordModel.id == rev.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = RevenueRecordModel(
                id=rev.id,
                source=rev.source,
                customer_id=rev.customer_id,
                product_service=rev.product_service,
                amount_cents=rev.amount_cents,
                currency=rev.currency,
                period_id=rev.period_id,
                invoice_id=rev.invoice_id,
                recognition_state=rev.recognition_state.value if hasattr(rev.recognition_state, "value") else str(rev.recognition_state),
                evidence_reference=rev.evidence_reference,
                verification_status=rev.verification_status,
                recorded_at=rev.recorded_at,
                metadata_json=rev.metadata,
            )
            self.session.add(m)
        else:
            m.recognition_state = rev.recognition_state.value if hasattr(rev.recognition_state, "value") else str(rev.recognition_state)
            m.verification_status = rev.verification_status

        await self.session.commit()
        return rev

    async def list_revenues(self) -> List[RevenueRecord]:
        stmt = select(RevenueRecordModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            RevenueRecord(
                id=m.id,
                source=m.source,
                customer_id=m.customer_id,
                product_service=m.product_service,
                amount_cents=m.amount_cents,
                currency=m.currency,
                period_id=m.period_id,
                invoice_id=m.invoice_id,
                recognition_state=RevenueRecognitionState(m.recognition_state),
                evidence_reference=m.evidence_reference,
                verification_status=m.verification_status,
                recorded_at=m.recorded_at,
                metadata=m.metadata_json or {},
            )
            for m in models
        ]

    # --- Expense Records ---
    async def save_expense(self, exp: ExpenseRecord) -> ExpenseRecord:
        stmt = select(ExpenseRecordModel).where(ExpenseRecordModel.id == exp.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ExpenseRecordModel(
                id=exp.id,
                vendor_id=exp.vendor_id,
                category=exp.category,
                amount_cents=exp.amount_cents,
                currency=exp.currency,
                incurred_date=exp.incurred_date,
                project_id=exp.project_id,
                department_id=exp.department_id,
                employee_id=exp.employee_id,
                purchase_order_id=exp.purchase_order_id,
                invoice_id=exp.invoice_id,
                approval_state=exp.approval_state.value if hasattr(exp.approval_state, "value") else str(exp.approval_state),
                evidence_reference=exp.evidence_reference,
                verification_status=exp.verification_status,
                reconciliation_status=exp.reconciliation_status.value if hasattr(exp.reconciliation_status, "value") else str(exp.reconciliation_status),
                metadata_json=exp.metadata,
            )
            self.session.add(m)
        else:
            m.approval_state = exp.approval_state.value if hasattr(exp.approval_state, "value") else str(exp.approval_state)
            m.verification_status = exp.verification_status
            m.reconciliation_status = exp.reconciliation_status.value if hasattr(exp.reconciliation_status, "value") else str(exp.reconciliation_status)

        await self.session.commit()
        return exp

    async def list_expenses(self) -> List[ExpenseRecord]:
        stmt = select(ExpenseRecordModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ExpenseRecord(
                id=m.id,
                vendor_id=m.vendor_id,
                category=m.category,
                amount_cents=m.amount_cents,
                currency=m.currency,
                incurred_date=m.incurred_date,
                project_id=m.project_id,
                department_id=m.department_id,
                employee_id=m.employee_id,
                purchase_order_id=m.purchase_order_id,
                invoice_id=m.invoice_id,
                approval_state=ExpenseApprovalState(m.approval_state),
                evidence_reference=m.evidence_reference,
                verification_status=m.verification_status,
                reconciliation_status=ReconciliationStatus(m.reconciliation_status),
                metadata=m.metadata_json or {},
            )
            for m in models
        ]

    # --- Payments ---
    async def save_payment(self, p: Payment) -> Payment:
        stmt = select(PaymentModel).where(PaymentModel.id == p.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = PaymentModel(
                id=p.id,
                invoice_id=p.invoice_id,
                amount_cents=p.amount_cents,
                currency=p.currency,
                payment_method=p.payment_method,
                counterparty=p.counterparty,
                external_reference=p.external_reference,
                status=p.status.value if hasattr(p.status, "value") else str(p.status),
                initiated_at=p.initiated_at,
                confirmed_at=p.confirmed_at,
                governance_approval_id=p.governance_approval_id,
                idempotency_key=p.idempotency_key,
                evidence_reference=p.evidence_reference,
                metadata_json=p.metadata,
            )
            self.session.add(m)
        else:
            m.status = p.status.value if hasattr(p.status, "value") else str(p.status)
            m.external_reference = p.external_reference
            m.confirmed_at = p.confirmed_at
            m.evidence_reference = p.evidence_reference

        await self.session.commit()
        return p

    async def get_payment_by_id(self, p_id: str) -> Optional[Payment]:
        stmt = select(PaymentModel).where(PaymentModel.id == p_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Payment(
            id=m.id,
            invoice_id=m.invoice_id,
            amount_cents=m.amount_cents,
            currency=m.currency,
            payment_method=m.payment_method,
            counterparty=m.counterparty,
            external_reference=m.external_reference,
            status=PaymentStatus(m.status),
            initiated_at=m.initiated_at,
            confirmed_at=m.confirmed_at,
            governance_approval_id=m.governance_approval_id,
            idempotency_key=m.idempotency_key,
            evidence_reference=m.evidence_reference,
            metadata=m.metadata_json or {},
        )

    async def get_payment_by_idempotency_key(self, key: str) -> Optional[Payment]:
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == key)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Payment(
            id=m.id,
            invoice_id=m.invoice_id,
            amount_cents=m.amount_cents,
            currency=m.currency,
            payment_method=m.payment_method,
            counterparty=m.counterparty,
            external_reference=m.external_reference,
            status=PaymentStatus(m.status),
            initiated_at=m.initiated_at,
            confirmed_at=m.confirmed_at,
            governance_approval_id=m.governance_approval_id,
            idempotency_key=m.idempotency_key,
            evidence_reference=m.evidence_reference,
            metadata=m.metadata_json or {},
        )

    async def list_payments(self) -> List[Payment]:
        stmt = select(PaymentModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Payment(
                id=m.id,
                invoice_id=m.invoice_id,
                amount_cents=m.amount_cents,
                currency=m.currency,
                payment_method=m.payment_method,
                counterparty=m.counterparty,
                external_reference=m.external_reference,
                status=PaymentStatus(m.status),
                initiated_at=m.initiated_at,
                confirmed_at=m.confirmed_at,
                governance_approval_id=m.governance_approval_id,
                idempotency_key=m.idempotency_key,
                evidence_reference=m.evidence_reference,
                metadata=m.metadata_json or {},
            )
            for m in models
        ]

    # --- Procurement ---
    async def save_procurement(self, req: ProcurementRequest) -> ProcurementRequest:
        stmt = select(ProcurementRequestModel).where(ProcurementRequestModel.id == req.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ProcurementRequestModel(
                id=req.id,
                requester_id=req.requester_id,
                department_id=req.department_id,
                vendor_id=req.vendor_id,
                item_description=req.item_description,
                estimated_cents=req.estimated_cents,
                currency=req.currency,
                status=req.status.value if hasattr(req.status, "value") else str(req.status),
                approval_governance_id=req.approval_governance_id,
                approver_id=req.approver_id,
                purchase_order_id=req.purchase_order_id,
                created_at=req.created_at,
                metadata_json=req.metadata,
            )
            self.session.add(m)
        else:
            m.status = req.status.value if hasattr(req.status, "value") else str(req.status)
            m.approver_id = req.approver_id
            m.purchase_order_id = req.purchase_order_id
            m.metadata_json = req.metadata

        await self.session.commit()
        return req

    async def get_procurement_by_id(self, req_id: str) -> Optional[ProcurementRequest]:
        stmt = select(ProcurementRequestModel).where(ProcurementRequestModel.id == req_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return ProcurementRequest(
            id=m.id,
            requester_id=m.requester_id,
            department_id=m.department_id,
            vendor_id=m.vendor_id,
            item_description=m.item_description,
            estimated_cents=m.estimated_cents,
            currency=m.currency,
            status=ProcurementStatus(m.status),
            approval_governance_id=m.approval_governance_id,
            approver_id=m.approver_id,
            purchase_order_id=m.purchase_order_id,
            created_at=m.created_at,
            metadata=m.metadata_json or {},
        )

    async def list_procurements(self) -> List[ProcurementRequest]:
        stmt = select(ProcurementRequestModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ProcurementRequest(
                id=m.id,
                requester_id=m.requester_id,
                department_id=m.department_id,
                vendor_id=m.vendor_id,
                item_description=m.item_description,
                estimated_cents=m.estimated_cents,
                currency=m.currency,
                status=ProcurementStatus(m.status),
                approval_governance_id=m.approval_governance_id,
                approver_id=m.approver_id,
                purchase_order_id=m.purchase_order_id,
                created_at=m.created_at,
                metadata=m.metadata_json or {},
            )
            for m in models
        ]

    # --- Budgets ---
    async def save_budget(self, budget: Budget) -> Budget:
        stmt = select(BudgetModel).where(BudgetModel.id == budget.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = BudgetModel(
                id=budget.id,
                name=budget.name,
                company_id=budget.company_id,
                department_id=budget.department_id,
                project_id=budget.project_id,
                period_name=budget.period_name,
                currency=budget.currency,
                allocated_cents=budget.allocated_cents,
                consumed_cents=budget.consumed_cents,
                status=budget.status,
                created_at=budget.created_at,
            )
            self.session.add(m)
        else:
            m.consumed_cents = budget.consumed_cents
            m.allocated_cents = budget.allocated_cents
            m.status = budget.status

        # Save allocations
        for alloc in budget.allocations:
            astmt = select(BudgetAllocationModel).where(BudgetAllocationModel.id == alloc.id)
            ares = await self.session.execute(astmt)
            am = ares.scalar_one_or_none()
            if am is None:
                am = BudgetAllocationModel(
                    id=alloc.id,
                    budget_id=budget.id,
                    category=alloc.category,
                    allocated_cents=alloc.allocated_cents,
                    consumed_cents=alloc.consumed_cents,
                    department_id=alloc.department_id,
                    project_id=alloc.project_id,
                )
                self.session.add(am)
            else:
                am.consumed_cents = alloc.consumed_cents

        await self.session.commit()
        return budget

    async def get_budget_by_id(self, budget_id: str) -> Optional[Budget]:
        stmt = select(BudgetModel).where(BudgetModel.id == budget_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None

        astmt = select(BudgetAllocationModel).where(BudgetAllocationModel.budget_id == budget_id)
        ares = await self.session.execute(astmt)
        alloc_models = ares.scalars().all()

        allocations = [
            BudgetAllocation(
                id=am.id,
                category=am.category,
                allocated_cents=am.allocated_cents,
                consumed_cents=am.consumed_cents,
                department_id=am.department_id,
                project_id=am.project_id,
            )
            for am in alloc_models
        ]

        return Budget(
            id=m.id,
            name=m.name,
            company_id=m.company_id,
            department_id=m.department_id,
            project_id=m.project_id,
            period_name=m.period_name,
            currency=m.currency,
            allocated_cents=m.allocated_cents,
            consumed_cents=m.consumed_cents,
            status=m.status,
            allocations=allocations,
            created_at=m.created_at,
        )

    async def list_budgets(self) -> List[Budget]:
        stmt = select(BudgetModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        results = []
        for m in models:
            astmt = select(BudgetAllocationModel).where(BudgetAllocationModel.budget_id == m.id)
            ares = await self.session.execute(astmt)
            alloc_models = ares.scalars().all()
            allocations = [
                BudgetAllocation(
                    id=am.id,
                    category=am.category,
                    allocated_cents=am.allocated_cents,
                    consumed_cents=am.consumed_cents,
                    department_id=am.department_id,
                    project_id=am.project_id,
                )
                for am in alloc_models
            ]
            results.append(
                Budget(
                    id=m.id,
                    name=m.name,
                    company_id=m.company_id,
                    department_id=m.department_id,
                    project_id=m.project_id,
                    period_name=m.period_name,
                    currency=m.currency,
                    allocated_cents=m.allocated_cents,
                    consumed_cents=m.consumed_cents,
                    status=m.status,
                    allocations=allocations,
                    created_at=m.created_at,
                )
            )
        return results

    # --- Reconciliations ---
    async def save_reconciliation(self, rec: Reconciliation) -> Reconciliation:
        stmt = select(ReconciliationModel).where(ReconciliationModel.id == rec.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ReconciliationModel(
                id=rec.id,
                period_id=rec.period_id,
                source_provider=rec.source_provider,
                status=rec.status.value if hasattr(rec.status, "value") else str(rec.status),
                total_matched_cents=rec.total_matched_cents,
                total_mismatched_cents=rec.total_mismatched_cents,
                conducted_at=rec.conducted_at,
            )
            self.session.add(m)
        else:
            m.status = rec.status.value if hasattr(rec.status, "value") else str(rec.status)
            m.total_matched_cents = rec.total_matched_cents
            m.total_mismatched_cents = rec.total_mismatched_cents

        for item in rec.items:
            istmt = select(ReconciliationItemModel).where(ReconciliationItemModel.id == item.id)
            ires = await self.session.execute(istmt)
            im = ires.scalar_one_or_none()
            if im is None:
                im = ReconciliationItemModel(
                    id=item.id,
                    reconciliation_id=rec.id,
                    internal_ref=item.internal_ref,
                    external_ref=item.external_ref,
                    internal_amount_cents=item.internal_amount_cents,
                    external_amount_cents=item.external_amount_cents,
                    currency=item.currency,
                    status=item.status.value if hasattr(item.status, "value") else str(item.status),
                    discrepancy_cents=item.discrepancy_cents,
                    resolution_notes=item.resolution_notes,
                )
                self.session.add(im)
            else:
                im.status = item.status.value if hasattr(item.status, "value") else str(item.status)
                im.discrepancy_cents = item.discrepancy_cents
                im.resolution_notes = item.resolution_notes

        await self.session.commit()
        return rec

    async def get_reconciliation_by_id(self, rec_id: str) -> Optional[Reconciliation]:
        stmt = select(ReconciliationModel).where(ReconciliationModel.id == rec_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None

        istmt = select(ReconciliationItemModel).where(ReconciliationItemModel.reconciliation_id == rec_id)
        ires = await self.session.execute(istmt)
        items_models = ires.scalars().all()

        items = [
            ReconciliationItem(
                id=im.id,
                internal_ref=im.internal_ref,
                external_ref=im.external_ref,
                internal_amount_cents=im.internal_amount_cents,
                external_amount_cents=im.external_amount_cents,
                currency=im.currency,
                status=ReconciliationStatus(im.status),
                discrepancy_cents=im.discrepancy_cents,
                resolution_notes=im.resolution_notes,
            )
            for im in items_models
        ]

        return Reconciliation(
            id=m.id,
            period_id=m.period_id,
            source_provider=m.source_provider,
            status=ReconciliationStatus(m.status),
            items=items,
            total_matched_cents=m.total_matched_cents,
            total_mismatched_cents=m.total_mismatched_cents,
            conducted_at=m.conducted_at,
        )

    async def list_reconciliations(self) -> List[Reconciliation]:
        stmt = select(ReconciliationModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        results = []
        for m in models:
            istmt = select(ReconciliationItemModel).where(ReconciliationItemModel.reconciliation_id == m.id)
            ires = await self.session.execute(istmt)
            items_models = ires.scalars().all()
            items = [
                ReconciliationItem(
                    id=im.id,
                    internal_ref=im.internal_ref,
                    external_ref=im.external_ref,
                    internal_amount_cents=im.internal_amount_cents,
                    external_amount_cents=im.external_amount_cents,
                    currency=im.currency,
                    status=ReconciliationStatus(im.status),
                    discrepancy_cents=im.discrepancy_cents,
                    resolution_notes=im.resolution_notes,
                )
                for im in items_models
            ]
            results.append(
                Reconciliation(
                    id=m.id,
                    period_id=m.period_id,
                    source_provider=m.source_provider,
                    status=ReconciliationStatus(m.status),
                    items=items,
                    total_matched_cents=m.total_matched_cents,
                    total_mismatched_cents=m.total_mismatched_cents,
                    conducted_at=m.conducted_at,
                )
            )
        return results

    # --- Metrics & Cash Flow ---
    async def save_metric(self, metric: BusinessMetric) -> BusinessMetric:
        stmt = select(BusinessMetricModel).where(BusinessMetricModel.id == metric.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = BusinessMetricModel(
                id=metric.id,
                metric_name=metric.metric_name,
                value_cents=metric.value_cents,
                numeric_value=metric.numeric_value,
                unit=metric.unit,
                recorded_at=metric.recorded_at,
                provenance_references_json=metric.provenance_references,
            )
            self.session.add(m)
        else:
            m.value_cents = metric.value_cents
            m.numeric_value = metric.numeric_value
            m.provenance_references_json = metric.provenance_references

        await self.session.commit()
        return metric

    async def list_metrics(self) -> List[BusinessMetric]:
        stmt = select(BusinessMetricModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            BusinessMetric(
                id=m.id,
                metric_name=m.metric_name,
                value_cents=m.value_cents,
                numeric_value=m.numeric_value,
                unit=m.unit,
                recorded_at=m.recorded_at,
                provenance_references=m.provenance_references_json or [],
            )
            for m in models
        ]

    async def save_cash_flow(self, snapshot: CashFlowSnapshot) -> CashFlowSnapshot:
        stmt = select(CashFlowSnapshotModel).where(CashFlowSnapshotModel.id == snapshot.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = CashFlowSnapshotModel(
                id=snapshot.id,
                snapshot_date=snapshot.snapshot_date,
                currency=snapshot.currency,
                actual_inflow_cents=snapshot.actual_inflow_cents,
                actual_outflow_cents=snapshot.actual_outflow_cents,
                expected_inflow_cents=snapshot.expected_inflow_cents,
                expected_outflow_cents=snapshot.expected_outflow_cents,
                committed_spending_cents=snapshot.committed_spending_cents,
                available_budget_cents=snapshot.available_budget_cents,
            )
            self.session.add(m)
        else:
            m.actual_inflow_cents = snapshot.actual_inflow_cents
            m.actual_outflow_cents = snapshot.actual_outflow_cents

        await self.session.commit()
        return snapshot

    async def get_latest_cash_flow(self) -> Optional[CashFlowSnapshot]:
        stmt = select(CashFlowSnapshotModel).order_by(desc(CashFlowSnapshotModel.snapshot_date)).limit(1)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return CashFlowSnapshot(
            id=m.id,
            snapshot_date=m.snapshot_date,
            currency=m.currency,
            actual_inflow_cents=m.actual_inflow_cents,
            actual_outflow_cents=m.actual_outflow_cents,
            expected_inflow_cents=m.expected_inflow_cents,
            expected_outflow_cents=m.expected_outflow_cents,
            committed_spending_cents=m.committed_spending_cents,
            available_budget_cents=m.available_budget_cents,
        )
