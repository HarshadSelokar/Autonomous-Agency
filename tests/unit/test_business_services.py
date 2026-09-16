"""
Unit tests for Phase 23 Business Operations engines & services.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.business import (
    BusinessTransaction,
    ProcurementStatus,
    ReconciliationStatus,
    TransactionType,
    Budget,
    BudgetAllocation,
)
from src.domain.exceptions import (
    UnauthorizedFinancialActionError,
    BudgetExceededError,
)
from src.domain.governance import RiskLevel
from src.infrastructure.database import Base
import src.infrastructure.models.business_model
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
from src.application.reconciliation_engine import ReconciliationEngine
from src.application.procurement_workflow_engine import ProcurementWorkflowEngine
from src.application.budget_control_engine import BudgetControlEngine
from src.application.business_governance_service import BusinessGovernanceService
from src.application.business_operations_service import BusinessOperationsService


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


def test_reconciliation_engine_matching_and_mismatch() -> None:
    engine = ReconciliationEngine()

    tx1 = BusinessTransaction(
        id="tx-1",
        transaction_type=TransactionType.REVENUE,
        amount_cents=100000,
        currency="USD",
        account_id="acc-1",
        counterparty="Acme Corp",
        external_reference="ext-ref-100",
    )
    tx2 = BusinessTransaction(
        id="tx-2",
        transaction_type=TransactionType.EXPENSE,
        amount_cents=50000,
        currency="USD",
        account_id="acc-1",
        counterparty="Cloud Vendor",
        external_reference="ext-ref-200",
    )

    statements = [
        {"external_ref": "ext-ref-100", "amount_cents": 100000, "currency": "USD"},
        {"external_ref": "ext-ref-200", "amount_cents": 45000, "currency": "USD"},  # Discrepancy: $500 vs $450
    ]

    rec = engine.reconcile_records([tx1, tx2], statements)

    assert rec.status == ReconciliationStatus.MISMATCH
    assert len(rec.items) == 2
    assert rec.items[0].status == ReconciliationStatus.MATCHED
    assert rec.items[1].status == ReconciliationStatus.MISMATCH
    assert rec.items[1].discrepancy_cents == 5000


def test_procurement_workflow_separation_of_duties() -> None:
    proc_engine = ProcurementWorkflowEngine()

    req = proc_engine.create_request(
        requester_id="emp-alice",
        item_description="High-performance AI GPU server",
        estimated_cents=500000,
        currency="USD",
    )

    # Requester attempting to approve their own request raises UnauthorizedFinancialActionError
    with pytest.raises(UnauthorizedFinancialActionError) as exc_info:
        proc_engine.approve_request(req, approver_id="emp-alice")
    assert "Separation of duties violation" in str(exc_info.value)

    # Different approver succeeds
    approved_req = proc_engine.approve_request(req, approver_id="mgr-bob")
    assert approved_req.status == ProcurementStatus.APPROVED

    po = proc_engine.generate_purchase_order(approved_req, "PO-2026-001", "vendor-1", "mgr-bob")
    assert po.po_number == "PO-2026-001"
    assert po.total_cents == 500000


def test_business_governance_risk_classification() -> None:
    gov = BusinessGovernanceService()

    # Read action
    assert gov.classify_risk("READ_REPORTS") == RiskLevel.LOW

    # Create draft
    assert gov.classify_risk("CREATE_DRAFT") == RiskLevel.MEDIUM

    # Send invoice under 50k
    assert gov.classify_risk("SEND_INVOICE", amount_cents=100000) == RiskLevel.HIGH

    # Send invoice over 50k
    assert gov.classify_risk("SEND_INVOICE", amount_cents=6000000) == RiskLevel.CRITICAL

    # Payment submission over governance requires approval
    with pytest.raises(UnauthorizedFinancialActionError):
        gov.evaluate_and_authorize("SUBMIT_PAYMENT", "emp-1", amount_cents=200000, approval_id=None)


@pytest.mark.asyncio
async def test_business_operations_service_flow(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)
    service = BusinessOperationsService(repository=repo)

    # 1. Record revenue
    rev = await service.record_revenue("SaaS Subscription", "cust-1", "Enterprise Plan", 250000, "USD")
    assert rev.amount_cents == 250000

    # 2. Create and issue invoice with governance approval
    inv = await service.create_invoice("cust-1", [{"description": "Enterprise SaaS", "quantity": 1, "unit_price_cents": 250000}])
    assert inv.total_cents == 250000

    issued_inv = await service.issue_and_send_invoice(inv.id, actor_id="mgr-bob", governance_approval_id="gov-app-100")
    assert issued_inv.status.value == "SENT"

    # 3. Request procurement
    proc_req = await service.request_procurement("emp-alice", "Developer Workstation", 300000, "USD")
    assert proc_req.status == ProcurementStatus.REQUESTED

    # 4. Approve procurement & issue PO
    po = await service.approve_procurement_and_issue_po(proc_req.id, approver_id="mgr-bob", vendor_id="vendor-dell", governance_approval_id="gov-app-101")
    assert po.po_number.startswith("PO-")
    assert po.total_cents == 300000
