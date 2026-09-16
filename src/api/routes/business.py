"""
FastAPI Routes for Phase 23 Business Operations & Financial Operations.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.business import (
    BusinessAccount,
    AccountType,
    TransactionType,
)
from src.domain.exceptions import (
    BudgetExceededError,
    FinancialPeriodClosedError,
    IdempotencyConflictError,
    ReconciliationMismatchError,
    UnauthorizedFinancialActionError,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
from src.application.business_operations_service import BusinessOperationsService

router = APIRouter(prefix="/business", tags=["business"])


def get_business_service(db: AsyncSession = Depends(get_db)) -> BusinessOperationsService:
    repo = SQLAlchemyBusinessRepository(db)
    return BusinessOperationsService(repository=repo)


# --- Request/Response Schemas ---
class CreateAccountRequest(BaseModel):
    account_code: str = Field(..., description="Unique chart-of-accounts code")
    name: str = Field(..., description="Account name")
    account_type: str = Field(default="OPERATING", description="Account type enum")
    currency: str = Field(default="USD", description="ISO 4217 currency")
    initial_balance_cents: int = Field(default=0, description="Initial balance in integer cents")
    department_id: Optional[str] = None


class RecordTransactionRequest(BaseModel):
    transaction_type: str = Field(..., description="Transaction type enum")
    amount_cents: int = Field(..., description="Monetary amount in cents")
    currency: str = Field(default="USD", description="Currency code")
    account_id: str = Field(..., description="Business account ID")
    counterparty: str = Field(..., description="Transaction counterparty name")
    source: str = Field(default="INTERNAL")
    external_reference: Optional[str] = None
    idempotency_key: Optional[str] = None
    evidence_reference: Optional[str] = None
    actor_id: str = Field(default="SYSTEM")


class RecordRevenueRequest(BaseModel):
    source: str
    customer_id: str
    product_service: str
    amount_cents: int
    currency: str = "USD"
    invoice_id: Optional[str] = None
    actor_id: str = "SYSTEM"


class RecordExpenseRequest(BaseModel):
    vendor_id: str
    category: str
    amount_cents: int
    currency: str = "USD"
    department_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    actor_id: str = "SYSTEM"


class CreateInvoiceRequest(BaseModel):
    customer_id: str
    lines: List[Dict[str, Any]]
    tax_cents: int = 0
    currency: str = "USD"
    idempotency_key: Optional[str] = None
    actor_id: str = "SYSTEM"


class IssueInvoiceRequest(BaseModel):
    actor_id: str
    governance_approval_id: Optional[str] = None


class SubmitPaymentRequest(BaseModel):
    counterparty: str
    amount_cents: int
    currency: str = "USD"
    invoice_id: Optional[str] = None
    external_reference: Optional[str] = None
    idempotency_key: Optional[str] = None
    governance_approval_id: Optional[str] = None
    actor_id: str = "SYSTEM"


class RequestProcurementRequest(BaseModel):
    requester_id: str
    item_description: str
    estimated_cents: int
    currency: str = "USD"
    department_id: Optional[str] = None
    vendor_id: Optional[str] = None


class ApproveProcurementRequest(BaseModel):
    approver_id: str
    vendor_id: str
    budget_id: Optional[str] = None
    governance_approval_id: Optional[str] = None


class RunReconciliationRequest(BaseModel):
    external_statements: List[Dict[str, Any]]
    source_provider: str = "EXTERNAL_BANK"


# --- Route Handlers ---

@router.get("/accounts")
async def list_accounts(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    accs = await service.repository.list_accounts()
    return [
        {
            "id": a.id,
            "account_code": a.account_code,
            "name": a.name,
            "account_type": a.account_type.value,
            "currency": a.currency,
            "balance_cents": a.balance_cents,
            "dollars": a.money_balance.to_dollars(),
            "department_id": a.department_id,
            "is_active": a.is_active,
        }
        for a in accs
    ]


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
async def create_account(
    req: CreateAccountRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    acc = BusinessAccount(
        account_code=req.account_code,
        name=req.name,
        account_type=AccountType(req.account_type.upper()),
        currency=req.currency,
        balance_cents=req.initial_balance_cents,
        department_id=req.department_id,
    )
    saved = await service.repository.save_account(acc)
    return {"id": saved.id, "account_code": saved.account_code, "name": saved.name}


@router.get("/transactions")
async def list_transactions(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    txs = await service.repository.list_transactions()
    return [
        {
            "id": t.id,
            "transaction_type": t.transaction_type.value,
            "amount_cents": t.amount_cents,
            "dollars": t.money_amount.to_dollars(),
            "currency": t.currency,
            "account_id": t.account_id,
            "counterparty": t.counterparty,
            "status": t.status.value,
            "reconciliation_status": t.reconciliation_status.value,
            "occurred_at": t.occurred_at.isoformat(),
        }
        for t in txs
    ]


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
async def record_transaction(
    req: RecordTransactionRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    try:
        tx = await service.record_transaction(
            transaction_type=TransactionType(req.transaction_type.upper()),
            amount_cents=req.amount_cents,
            currency=req.currency,
            account_id=req.account_id,
            counterparty=req.counterparty,
            source=req.source,
            external_reference=req.external_reference,
            idempotency_key=req.idempotency_key,
            evidence_reference=req.evidence_reference,
            actor_id=req.actor_id,
        )
        return {"id": tx.id, "status": tx.status.value, "amount_cents": tx.amount_cents}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/revenue")
async def list_revenue(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    revs = await service.repository.list_revenues()
    return [
        {
            "id": r.id,
            "source": r.source,
            "customer_id": r.customer_id,
            "amount_cents": r.amount_cents,
            "currency": r.currency,
            "recognition_state": r.recognition_state.value,
        }
        for r in revs
    ]


@router.post("/revenue", status_code=status.HTTP_201_CREATED)
async def record_revenue(
    req: RecordRevenueRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    rev = await service.record_revenue(
        source=req.source,
        customer_id=req.customer_id,
        product_service=req.product_service,
        amount_cents=req.amount_cents,
        currency=req.currency,
        invoice_id=req.invoice_id,
        actor_id=req.actor_id,
    )
    return {"id": rev.id, "amount_cents": rev.amount_cents}


@router.get("/expenses")
async def list_expenses(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    exps = await service.repository.list_expenses()
    return [
        {
            "id": e.id,
            "vendor_id": e.vendor_id,
            "category": e.category,
            "amount_cents": e.amount_cents,
            "currency": e.currency,
            "approval_state": e.approval_state.value,
        }
        for e in exps
    ]


@router.post("/expenses", status_code=status.HTTP_201_CREATED)
async def record_expense(
    req: RecordExpenseRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    exp = await service.record_expense(
        vendor_id=req.vendor_id,
        category=req.category,
        amount_cents=req.amount_cents,
        currency=req.currency,
        department_id=req.department_id,
        purchase_order_id=req.purchase_order_id,
        actor_id=req.actor_id,
    )
    return {"id": exp.id, "amount_cents": exp.amount_cents}


@router.get("/invoices")
async def list_invoices(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    invs = await service.repository.list_invoices()
    return [
        {
            "id": i.id,
            "invoice_number": i.invoice_number,
            "customer_id": i.customer_id,
            "total_cents": i.total_cents,
            "status": i.status.value,
            "issue_date": i.issue_date.isoformat(),
        }
        for i in invs
    ]


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    req: CreateInvoiceRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    inv = await service.create_invoice(
        customer_id=req.customer_id,
        lines=req.lines,
        tax_cents=req.tax_cents,
        currency=req.currency,
        idempotency_key=req.idempotency_key,
        actor_id=req.actor_id,
    )
    return {"id": inv.id, "invoice_number": inv.invoice_number, "total_cents": inv.total_cents}


@router.post("/invoices/{id}/issue")
async def issue_invoice(
    id: str,
    req: IssueInvoiceRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    try:
        inv = await service.issue_and_send_invoice(
            invoice_id=id,
            actor_id=req.actor_id,
            governance_approval_id=req.governance_approval_id,
        )
        return {"id": inv.id, "status": inv.status.value}
    except UnauthorizedFinancialActionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/payments")
async def list_payments(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    pmts = await service.repository.list_payments()
    return [
        {
            "id": p.id,
            "counterparty": p.counterparty,
            "amount_cents": p.amount_cents,
            "status": p.status.value,
        }
        for p in pmts
    ]


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def submit_payment(
    req: SubmitPaymentRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    try:
        p = await service.record_payment(
            counterparty=req.counterparty,
            amount_cents=req.amount_cents,
            currency=req.currency,
            invoice_id=req.invoice_id,
            external_reference=req.external_reference,
            idempotency_key=req.idempotency_key,
            governance_approval_id=req.governance_approval_id,
            actor_id=req.actor_id,
        )
        return {"id": p.id, "status": p.status.value, "amount_cents": p.amount_cents}
    except UnauthorizedFinancialActionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/procurement")
async def list_procurement(service: BusinessOperationsService = Depends(get_business_service)) -> List[Dict[str, Any]]:
    procs = await service.repository.list_procurements()
    return [
        {
            "id": p.id,
            "requester_id": p.requester_id,
            "item_description": p.item_description,
            "estimated_cents": p.estimated_cents,
            "status": p.status.value,
        }
        for p in procs
    ]


@router.post("/procurement", status_code=status.HTTP_201_CREATED)
async def request_procurement(
    req: RequestProcurementRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    p = await service.request_procurement(
        requester_id=req.requester_id,
        item_description=req.item_description,
        estimated_cents=req.estimated_cents,
        currency=req.currency,
        department_id=req.department_id,
        vendor_id=req.vendor_id,
    )
    return {"id": p.id, "status": p.status.value}


@router.post("/procurement/{id}/approve")
async def approve_procurement(
    id: str,
    req: ApproveProcurementRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    try:
        po = await service.approve_procurement_and_issue_po(
            request_id=id,
            approver_id=req.approver_id,
            vendor_id=req.vendor_id,
            budget_id=req.budget_id,
            governance_approval_id=req.governance_approval_id,
        )
        return {"purchase_order_id": po.id, "po_number": po.po_number, "status": po.status}
    except UnauthorizedFinancialActionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BudgetExceededError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/reconciliation")
async def run_reconciliation(
    req: RunReconciliationRequest,
    service: BusinessOperationsService = Depends(get_business_service),
) -> Dict[str, Any]:
    rec = await service.run_reconciliation(req.external_statements, req.source_provider)
    return {
        "id": rec.id,
        "status": rec.status.value,
        "total_matched_cents": rec.total_matched_cents,
        "total_mismatched_cents": rec.total_mismatched_cents,
        "items_count": len(rec.items),
    }


@router.get("/cash-flow")
async def get_cash_flow(service: BusinessOperationsService = Depends(get_business_service)) -> Dict[str, Any]:
    snapshot = await service.get_cash_flow_snapshot()
    return {
        "id": snapshot.id,
        "actual_inflow_cents": snapshot.actual_inflow_cents,
        "actual_outflow_cents": snapshot.actual_outflow_cents,
        "net_actual_cash_cents": snapshot.net_actual_cash_cents,
        "expected_inflow_cents": snapshot.expected_inflow_cents,
        "expected_outflow_cents": snapshot.expected_outflow_cents,
        "available_budget_cents": snapshot.available_budget_cents,
    }
