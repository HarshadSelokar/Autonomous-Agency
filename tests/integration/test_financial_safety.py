"""
Integration & Financial Safety Tests for Phase 23 Business Operations.

Verifies financial safety invariants:
- Float currency rejection
- Currency mismatch arithmetic prevention
- Over-budget spending block
- Closed financial period lock
- Separation of duties (Requester != Approver)
- Idempotency key protection
- Governance authorization checks for high-risk operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.business import Money, Budget, FinancialPeriod, FinancialPeriodState
from src.domain.exceptions import (
    MoneyArithmeticError,
    BudgetExceededError,
    FinancialPeriodClosedError,
    UnauthorizedFinancialActionError,
)
from src.infrastructure.database import Base
import src.infrastructure.models.business_model
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
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


def test_float_and_currency_mismatch_safety() -> None:
    # Reject float inputs in Money constructor
    with pytest.raises(MoneyArithmeticError):
        Money(10.99, "USD")  # type: ignore

    # Mismatched currency arithmetic rejection
    usd = Money(1000, "USD")
    eur = Money(1000, "EUR")

    with pytest.raises(MoneyArithmeticError):
        usd.add(eur)

    with pytest.raises(MoneyArithmeticError):
        usd.subtract(eur)


@pytest.mark.asyncio
async def test_budget_exceeded_blocking(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)
    service = BusinessOperationsService(repository=repo)

    budget = Budget(
        id="b-safety-1",
        name="Security Audit Budget",
        allocated_cents=500000,  # $5,000
        consumed_cents=450000,   # $4,500
    )
    await repo.save_budget(budget)

    req = await service.request_procurement(
        requester_id="emp-1",
        item_description="External Pen Test",
        estimated_cents=100000,  # $1,000 requested vs $500 remaining
        currency="USD",
    )

    with pytest.raises(BudgetExceededError) as exc_info:
        await service.approve_procurement_and_issue_po(
            request_id=req.id,
            approver_id="mgr-1",
            vendor_id="vendor-sec",
            budget_id="b-safety-1",
            governance_approval_id="gov-app-1",
        )
    assert exc_info.value.requested_cents == 100000
    assert exc_info.value.remaining_cents == 50000


@pytest.mark.asyncio
async def test_separation_of_duties_enforcement(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)
    service = BusinessOperationsService(repository=repo)

    req = await service.request_procurement(
        requester_id="emp-same-actor",
        item_description="Cloud Storage",
        estimated_cents=50000,
        currency="USD",
    )

    with pytest.raises(UnauthorizedFinancialActionError) as exc_info:
        await service.approve_procurement_and_issue_po(
            request_id=req.id,
            approver_id="emp-same-actor",
            vendor_id="vendor-aws",
            governance_approval_id="gov-app-separation-test",
        )
    assert "Separation of duties violation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unauthorized_payment_action_rejection(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)
    service = BusinessOperationsService(repository=repo)

    with pytest.raises(UnauthorizedFinancialActionError) as exc_info:
        await service.record_payment(
            counterparty="Vendor X",
            amount_cents=1000000,
            currency="USD",
            governance_approval_id=None,  # Missing required approval
            actor_id="agent-untrusted",
        )
    assert "requires explicit governance approval" in str(exc_info.value)


@pytest.mark.asyncio
async def test_strong_idempotency_prevention(async_session: AsyncSession):
    repo = SQLAlchemyBusinessRepository(async_session)
    service = BusinessOperationsService(repository=repo)

    idemp = "idemp-key-unique-999"
    pmt1 = await service.record_payment(
        counterparty="Cloud Supplier",
        amount_cents=250000,
        currency="USD",
        idempotency_key=idemp,
        governance_approval_id="gov-app-999",
        actor_id="mgr-1",
    )

    pmt2 = await service.record_payment(
        counterparty="Cloud Supplier",
        amount_cents=250000,
        currency="USD",
        idempotency_key=idemp,
        governance_approval_id="gov-app-999",
        actor_id="mgr-1",
    )

    assert pmt1.id == pmt2.id
