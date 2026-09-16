# Phase 23 — Autonomous Business Operations Domain Architecture

## Overview
Phase 23 introduces the business-operations domain into the Autonomous Company OS. This layer allows autonomous AI agents, employees, and swarms to reason about, manage, and execute operational business workflows—including revenue, expenses, budgets, procurement, invoices, subscriptions, and financial metrics—without violating strict financial authority boundaries.

## Core Principle
Financial and business data are high-trust organizational information. Autonomous reasoning or AI models MUST NOT directly create authoritative financial reality.

```
CLAIM != TRANSACTION
TRANSACTION != VERIFIED TRANSACTION
VERIFIED TRANSACTION != AUTHORIZED PAYMENT
RECOMMENDATION != DECISION
DECISION != EXECUTION
EXECUTION != SETTLEMENT
SETTLEMENT != RECONCILIATION
ACTUAL != EXPECTED != FORECAST != CASH
```

## Architectural Lifecycle

```
BUSINESS EVENT 
  → BUSINESS PROCESS 
  → DECISION 
  → GOVERNANCE 
  → EXECUTION 
  → EVIDENCE 
  → VERIFICATION 
  → RECONCILIATION 
  → REPORTING 
  → LEARNING
```

## Domain Entities
- **`Money`**: Fixed-precision value object (`amount_cents: int`, `currency: str = "USD"`). Never uses floating-point arithmetic.
- **`BusinessAccount`**: Abstract ledger account for tracking operating balances, accounts receivable, and payables.
- **`BusinessTransaction`**: Structured transaction record with lifecycle (`RECORDED` -> `VALIDATING` -> `VERIFIED` -> `RECONCILED`).
- **`RevenueRecord`**: Records revenue with recognition states (`EXPECTED`, `INVOICED`, `RECEIVED`, `VERIFIED`).
- **`ExpenseRecord`**: Incurred operational costs mapped to vendors, projects, and departments.
- **`Invoice` & `InvoiceLine`**: Formatted customer billing document with tax, subtotal, line items, and governance approvals.
- **`Payment`**: Governed external payment submission with idempotency keys.
- **`ProcurementRequest` & `PurchaseOrder`**: Governed procurement workflow enforcing Separation of Duties (`Requester != Approver`).
- **`Budget` & `BudgetAllocation`**: Department and project budget allocations with deterministic consumption checks (`remaining = allocated - consumed`).
- **`Reconciliation` & `ReconciliationItem`**: Provider-neutral reconciliation engine comparing internal records vs external provider statements.
- **`CashFlowSnapshot`**: Multi-dimensional cash position tracking (`actual_inflow`, `actual_outflow`, `expected_inflow`, `available_budget`).

## Security & Governance Invariants
1. **No Autonomous Money Movement**: External financial transfers require explicit human governance approval and policy check.
2. **Separation of Duties**: Requesters cannot approve their own procurement requests or purchase orders.
3. **Idempotency Keys**: All financial transactions, payments, and invoices accept deterministic idempotency keys (`company_id + operation + source_ref`).
