"""
Unit tests for SQLAlchemy Business Repository (Phase 23).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.business import (
    BusinessAccount,
    BusinessTransaction,
    Invoice,
    InvoiceLine,
    Budget,
    BudgetAllocation,
    Reconciliation,
    ReconciliationItem,
    CashFlowSnapshot,
    AccountType,
    TransactionType,
    TransactionStatus,
    InvoiceStatus,
    ReconciliationStatus,
)
from src.infrastructure.database import Base
import src.infrastructure.models.business_model  # Ensure models registered
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_business_account_repository_crud(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)

    acc = BusinessAccount(
        id="acc-100",
        account_code="1000-OPERATING",
        name="Main Operating Account",
        account_type=AccountType.OPERATING,
        currency="USD",
        balance_cents=5000000,
    )
    saved = await repo.save_account(acc)
    assert saved.id == "acc-100"

    fetched = await repo.get_account_by_id("acc-100")
    assert fetched is not None
    assert fetched.name == "Main Operating Account"
    assert fetched.balance_cents == 5000000

    all_accs = await repo.list_accounts()
    assert len(all_accs) == 1


@pytest.mark.asyncio
async def test_business_transaction_idempotency(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)

    tx = BusinessTransaction(
        id="tx-100",
        transaction_type=TransactionType.EXPENSE,
        amount_cents=150000,
        currency="USD",
        account_id="acc-100",
        counterparty="Cloud Hosting Inc",
        idempotency_key="idemp-key-777",
    )
    await repo.save_transaction(tx)

    by_key = await repo.get_transaction_by_idempotency_key("idemp-key-777")
    assert by_key is not None
    assert by_key.id == "tx-100"
    assert by_key.amount_cents == 150000


@pytest.mark.asyncio
async def test_invoice_repository_crud(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)

    line1 = InvoiceLine(id="line-1", description="Consulting Services", quantity=10, unit_price_cents=15000, subtotal_cents=150000)
    inv = Invoice(
        id="inv-100",
        invoice_number="INV-2026-999",
        customer_id="cust-888",
        line_items=[line1],
        subtotal_cents=150000,
        tax_cents=15000,
        total_cents=165000,
        currency="USD",
        status=InvoiceStatus.ISSUED,
    )

    await repo.save_invoice(inv)

    fetched = await repo.get_invoice_by_id("inv-100")
    assert fetched is not None
    assert fetched.invoice_number == "INV-2026-999"
    assert len(fetched.line_items) == 1
    assert fetched.line_items[0].description == "Consulting Services"


@pytest.mark.asyncio
async def test_budget_and_reconciliation_crud(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)

    b_alloc = BudgetAllocation(id="alloc-1", category="Cloud Infra", allocated_cents=500000, consumed_cents=100000)
    budget = Budget(
        id="b-100",
        name="Q3 Infrastructure",
        allocated_cents=500000,
        consumed_cents=100000,
        allocations=[b_alloc],
    )
    await repo.save_budget(budget)

    fetched_b = await repo.get_budget_by_id("b-100")
    assert fetched_b is not None
    assert fetched_b.name == "Q3 Infrastructure"
    assert len(fetched_b.allocations) == 1

    rec_item = ReconciliationItem(
        id="rec-item-1",
        internal_ref="tx-100",
        external_ref="ext-stmt-555",
        internal_amount_cents=100000,
        external_amount_cents=100000,
        status=ReconciliationStatus.MATCHED,
    )
    rec = Reconciliation(
        id="rec-100",
        status=ReconciliationStatus.MATCHED,
        items=[rec_item],
        total_matched_cents=100000,
    )
    await repo.save_reconciliation(rec)

    fetched_rec = await repo.get_reconciliation_by_id("rec-100")
    assert fetched_rec is not None
    assert fetched_rec.status == ReconciliationStatus.MATCHED
    assert len(fetched_rec.items) == 1
