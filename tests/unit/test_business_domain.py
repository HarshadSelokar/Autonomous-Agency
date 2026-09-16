"""
Unit tests for Business Operations domain models & money representation (Phase 23).
"""

import pytest
from datetime import datetime, UTC

from src.domain.business import (
    Money,
    AccountType,
    TransactionType,
    TransactionStatus,
    InvoiceStatus,
    PaymentStatus,
    ReconciliationStatus,
    FinancialPeriodState,
    BusinessAccount,
    BusinessTransaction,
    RevenueRecord,
    ExpenseRecord,
    Invoice,
    InvoiceLine,
    Budget,
    FinancialPeriod,
    CashFlowSnapshot,
)
from src.domain.exceptions import (
    MoneyArithmeticError,
    BudgetExceededError,
    FinancialPeriodClosedError,
)


def test_money_value_object_validations() -> None:
    # Deterministic integer cents
    m1 = Money(1000, "USD")
    assert m1.amount_cents == 1000
    assert m1.currency == "USD"
    assert m1.to_dollars() == 10.0

    # From dollars
    m2 = Money.from_dollars(19.99, "USD")
    assert m2.amount_cents == 1999
    assert m2.to_dollars() == 19.99

    # Rejection of float amount_cents
    with pytest.raises(MoneyArithmeticError):
        Money(10.5, "USD")  # type: ignore

    # Currency uppercase auto-formatting
    m3 = Money(500, "usd")
    assert m3.currency == "USD"

    # Invalid currency format
    with pytest.raises(MoneyArithmeticError):
        Money(500, "US")


def test_money_arithmetic() -> None:
    m1 = Money(1000, "USD")
    m2 = Money(500, "USD")

    # Add & Subtract
    sum_m = m1.add(m2)
    assert sum_m.amount_cents == 1500

    sub_m = m1.subtract(m2)
    assert sub_m.amount_cents == 500

    # Multiply
    mult_m = m1.multiply(1.5)
    assert mult_m.amount_cents == 1500

    # Mismatched currency error
    eur = Money(500, "EUR")
    with pytest.raises(MoneyArithmeticError):
        m1.add(eur)

    with pytest.raises(MoneyArithmeticError):
        m1.subtract(eur)


def test_invoice_total_calculation() -> None:
    line1 = InvoiceLine(description="Consulting", quantity=5, unit_price_cents=10000)
    line2 = InvoiceLine(description="Software License", quantity=1, unit_price_cents=25000)
    
    invoice = Invoice(
        invoice_number="INV-2026-001",
        customer_id="cust-123",
        line_items=[line1, line2],
        tax_cents=5000,
        currency="USD",
    )
    invoice.recalculate_totals()
    assert invoice.subtotal_cents == 75000  # (5*10000) + (1*25000)
    assert invoice.total_cents == 80000     # 75000 + 5000


def test_budget_consumption_and_invariant() -> None:
    budget = Budget(
        name="Engineering Q3",
        allocated_cents=1000000,  # $10,000
        consumed_cents=200000,   # $2,000
    )
    assert budget.remaining_cents == 800000

    # Valid consumption
    budget.consume(300000)
    assert budget.consumed_cents == 500000
    assert budget.remaining_cents == 500000

    # Over-consumption raises BudgetExceededError
    with pytest.raises(BudgetExceededError) as exc_info:
        budget.consume(600000)
    assert exc_info.value.requested_cents == 600000
    assert exc_info.value.remaining_cents == 500000


def test_financial_period_closing_invariant() -> None:
    period = FinancialPeriod(
        period_name="2026-Q2",
        state=FinancialPeriodState.CLOSED,
    )
    with pytest.raises(FinancialPeriodClosedError):
        period.ensure_open()


def test_cash_flow_snapshot_calculation() -> None:
    snapshot = CashFlowSnapshot(
        actual_inflow_cents=500000,
        actual_outflow_cents=300000,
        expected_inflow_cents=200000,
        expected_outflow_cents=100000,
    )
    assert snapshot.net_actual_cash_cents == 200000
