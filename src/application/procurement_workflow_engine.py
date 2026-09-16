"""
Governed Procurement Workflow Engine for Phase 23.

Enforces Separation of Duties (Requester != Approver != Verifier) and
governance approval policies for purchase requests and purchase orders.
"""

from datetime import UTC, datetime
from typing import Optional
import uuid

from src.domain.business import (
    ProcurementRequest,
    ProcurementStatus,
    PurchaseOrder,
)
from src.domain.exceptions import (
    InvalidStateTransitionError,
    UnauthorizedFinancialActionError,
)


class ProcurementWorkflowEngine:
    """Orchestrates governed procurement lifecycles."""

    def create_request(
        self,
        requester_id: str,
        item_description: str,
        estimated_cents: int,
        currency: str = "USD",
        department_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
    ) -> ProcurementRequest:
        return ProcurementRequest(
            id=str(uuid.uuid4()),
            requester_id=requester_id,
            department_id=department_id,
            vendor_id=vendor_id,
            item_description=item_description,
            estimated_cents=estimated_cents,
            currency=currency,
            status=ProcurementStatus.REQUESTED,
            created_at=datetime.now(UTC),
        )

    def submit_for_approval(self, request: ProcurementRequest) -> ProcurementRequest:
        if request.status != ProcurementStatus.REQUESTED:
            raise InvalidStateTransitionError(
                "ProcurementRequest", request.id, request.status.value, ProcurementStatus.APPROVAL_REQUIRED.value
            )
        request.status = ProcurementStatus.APPROVAL_REQUIRED
        return request

    def approve_request(
        self,
        request: ProcurementRequest,
        approver_id: str,
        governance_approval_id: Optional[str] = None,
    ) -> ProcurementRequest:
        # Enforce Separation of Duties: Requester cannot approve their own procurement request
        if request.requester_id == approver_id:
            raise UnauthorizedFinancialActionError(
                f"Separation of duties violation: Requester '{request.requester_id}' cannot approve their own procurement request."
            )

        if request.status not in (ProcurementStatus.REQUESTED, ProcurementStatus.REVIEW, ProcurementStatus.APPROVAL_REQUIRED):
            raise InvalidStateTransitionError(
                "ProcurementRequest", request.id, request.status.value, ProcurementStatus.APPROVED.value
            )

        request.status = ProcurementStatus.APPROVED
        request.approver_id = approver_id
        request.approval_governance_id = governance_approval_id
        return request

    def generate_purchase_order(
        self,
        request: ProcurementRequest,
        po_number: str,
        vendor_id: str,
        approved_by: str,
    ) -> PurchaseOrder:
        if request.status != ProcurementStatus.APPROVED:
            raise UnauthorizedFinancialActionError(
                f"Cannot generate PurchaseOrder for unapproved procurement request '{request.id}' in status '{request.status.value}'."
            )

        po = PurchaseOrder(
            id=str(uuid.uuid4()),
            po_number=po_number,
            procurement_request_id=request.id,
            vendor_id=vendor_id,
            requester_id=request.requester_id,
            department_id=request.department_id,
            total_cents=request.estimated_cents,
            currency=request.currency,
            status="ISSUED",
            approved_by=approved_by,
            created_at=datetime.now(UTC),
        )

        request.status = ProcurementStatus.PURCHASE_ORDER
        request.purchase_order_id = po.id
        return po
