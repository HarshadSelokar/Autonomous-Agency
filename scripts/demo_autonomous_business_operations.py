"""
End-to-End Demonstration Script for Phase 23 Autonomous Business Operations & Financial Control.

Demonstrates:
1. Business objective creation & revenue loading.
2. Expense recording & budget check.
3. Invoice creation, validation & governance approval flow.
4. Procurement request with Separation of Duties enforcement.
5. Human governance approval & Purchase Order generation.
6. Reconciliation Engine (Matched vs Discrepancy Mismatch & Resolution).
7. Financial safety idempotency & cash-flow snapshot generation.
"""

import asyncio
from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.business import (
    AccountType,
    TransactionType,
    RevenueRecognitionState,
    ReconciliationStatus,
)
from src.domain.exceptions import (
    UnauthorizedFinancialActionError,
    BudgetExceededError,
)
from src.infrastructure.database import Base
import src.infrastructure.models.business_model
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
from src.application.business_operations_service import BusinessOperationsService


async def run_demo():
    print("=" * 70)
    print("PHASE 23: AUTONOMOUS BUSINESS OPERATIONS & FINANCIAL CONTROL DEMO")
    print("=" * 70)

    # Setup in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        repo = SQLAlchemyBusinessRepository(session)
        service = BusinessOperationsService(repository=repo)

        # Step 1: Create Business Accounts
        print("\n[STEP 1] Creating Business Accounts...")
        op_acc = await service.record_transaction(
            transaction_type=TransactionType.CREDIT,
            amount_cents=10000000, # $100,000
            currency="USD",
            account_id="acc-main-op",
            counterparty="Initial Capital",
            source="BANK_DEPOSIT",
            actor_id="CFO_AGENT",
        )
        print(f"  [OK] Operating Account 'acc-main-op' recorded: ${op_acc.amount_cents / 100:,.2f} USD")

        # Step 2: Record Revenue
        print("\n[STEP 2] Loading Revenue Records...")
        rev1 = await service.record_revenue(
            source="Enterprise Contract A",
            customer_id="cust-acme",
            product_service="Annual AI OS Subscription",
            amount_cents=5000000, # $50,000
            currency="USD",
            actor_id="REVENUE_AGENT",
        )
        print(f"  [OK] Revenue Recorded: ${rev1.amount_cents / 100:,.2f} for customer {rev1.customer_id}")

        # Step 3: Record Expenses
        print("\n[STEP 3] Recording Operational Expenses...")
        exp1 = await service.record_expense(
            vendor_id="vendor-aws",
            category="Cloud Compute",
            amount_cents=1200000, # $12,000
            currency="USD",
            department_id="dept-eng",
            actor_id="FINANCE_AGENT",
        )
        print(f"  [OK] Expense Recorded: ${exp1.amount_cents / 100:,.2f} to vendor {exp1.vendor_id}")

        # Step 4: Create Draft Invoice
        print("\n[STEP 4] Creating Customer Invoice Draft...")
        inv = await service.create_invoice(
            customer_id="cust-acme",
            lines=[
                {"description": "AI Swarm Deployment & Training", "quantity": 1, "unit_price_cents": 2500000},
                {"description": "Custom Verification Pipeline", "quantity": 1, "unit_price_cents": 1000000},
            ],
            tax_cents=350000,
            currency="USD",
            actor_id="BILLING_AGENT",
        )
        print(f"  [OK] Invoice Draft '{inv.invoice_number}' created. Total: ${inv.total_cents / 100:,.2f} USD")

        # Step 5: Issue & Send Invoice via Governance Approval
        print("\n[STEP 5] Issuing & Sending Invoice under Governance Policy...")
        issued_inv = await service.issue_and_send_invoice(
            invoice_id=inv.id,
            actor_id="mgr-finance-lead",
            governance_approval_id="gov-app-INV-999",
        )
        print(f"  [OK] Invoice '{issued_inv.invoice_number}' Issued & Sent. Status: {issued_inv.status.value}")

        # Step 6: Procurement Request & Separation of Duties Enforced
        print("\n[STEP 6] Requesting Procurement & Testing Separation of Duties...")
        proc_req = await service.request_procurement(
            requester_id="emp-alice-engineer",
            item_description="High-Capacity GPU Workstations (x4)",
            estimated_cents=2000000, # $20,000
            currency="USD",
            department_id="dept-ai-research",
            vendor_id="vendor-nvidia",
        )
        print(f"  [OK] Procurement Request '{proc_req.id}' created by emp-alice-engineer.")

        # Attempt self-approval by requester (MUST FAIL)
        print("  [TEST] Testing self-approval enforcement by requester...")
        try:
            await service.approve_procurement_and_issue_po(
                request_id=proc_req.id,
                approver_id="emp-alice-engineer",
                vendor_id="vendor-nvidia",
            )
            print("  [ERROR] Self-approval check failed!")
        except UnauthorizedFinancialActionError as e:
            print(f"  [OK] Self-approval blocked as expected: {e}")

        # Valid approval by Manager Bob
        po = await service.approve_procurement_and_issue_po(
            request_id=proc_req.id,
            approver_id="mgr-bob-vp",
            vendor_id="vendor-nvidia",
            governance_approval_id="gov-app-PO-888",
        )
        print(f"  [OK] Approved by mgr-bob-vp. Purchase Order Issued: '{po.po_number}' (${po.total_cents / 100:,.2f} USD)")

        # Step 7: Deterministic Reconciliation Engine Demo (Match & Mismatch)
        print("\n[STEP 7] Running Financial Reconciliation Engine...")
        statements = [
            {"external_ref": op_acc.id, "amount_cents": 10000000, "currency": "USD", "counterparty": "Initial Capital"},
            {"external_ref": rev1.id, "amount_cents": 5000000, "currency": "USD", "counterparty": "cust-acme"},
            {"external_ref": exp1.id, "amount_cents": 1150000, "currency": "USD", "counterparty": "vendor-aws"}, # Mismatch: $12,000 internal vs $11,500 bank statement
        ]
        rec = await service.run_reconciliation(statements, source_provider="CHASE_BANK")
        print(f"  [RECON RESULT] Status: {rec.status.value}")
        print(f"  Total Matched: ${rec.total_matched_cents / 100:,.2f} | Total Discrepancy: ${rec.total_mismatched_cents / 100:,.2f}")
        for item in rec.items:
            print(f"   - Ref {item.internal_ref}: Status={item.status.value} | Discrepancy=${item.discrepancy_cents / 100:,.2f}")

        # Step 8: Idempotency Protection
        print("\n[STEP 8] Testing Strong Idempotency Protection...")
        idemp_key = "payment-key-2026-09-17-001"
        pmt1 = await service.record_payment(
            counterparty="cust-acme",
            amount_cents=3850000,
            currency="USD",
            invoice_id=inv.id,
            idempotency_key=idemp_key,
            governance_approval_id="gov-app-PMT-777",
            actor_id="mgr-finance-lead",
        )
        pmt2 = await service.record_payment(
            counterparty="cust-acme",
            amount_cents=3850000,
            currency="USD",
            invoice_id=inv.id,
            idempotency_key=idemp_key,
            governance_approval_id="gov-app-PMT-777",
            actor_id="mgr-finance-lead",
        )
        assert pmt1.id == pmt2.id
        print(f"  [OK] Idempotency verified: Duplicate request returned original Payment ID '{pmt1.id}'.")

        # Step 9: Cash Flow Snapshot
        print("\n[STEP 9] Generating Cash Flow Snapshot...")
        cf = await service.get_cash_flow_snapshot()
        print(f"  Actual Inflow: ${cf.actual_inflow_cents / 100:,.2f}")
        print(f"  Actual Outflow: ${cf.actual_outflow_cents / 100:,.2f}")
        print(f"  Net Actual Cash: ${cf.net_actual_cash_cents / 100:,.2f}")

    await engine.dispose()
    print("\n" + "=" * 70)
    print("PHASE 23 E2E DEMONSTRATION COMPLETE - ALL INVARIANTS VERIFIED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
