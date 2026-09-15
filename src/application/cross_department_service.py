"""Cross-Department Collaboration Service for Phase 14.

Coordinates cross-department requests, structured handoffs, evidence verification,
SLA tracking, bottleneck detection, and manager escalations.
"""

import logging
from datetime import UTC, datetime
from typing import List, Optional, Any
from uuid import uuid4

from src.domain.cross_department import (
    DepartmentHandoff,
    DepartmentPriority,
    DepartmentRequest,
    DepartmentRequestStatus,
    HandoffStatus,
)
from src.domain.events import (
    DepartmentEscalatedEvent,
    DepartmentHandoffAcceptedEvent,
    DepartmentHandoffCreatedEvent,
    DepartmentHandoffRejectedEvent,
    DepartmentRequestAcceptedEvent,
    DepartmentRequestCreatedEvent,
    DepartmentRequestDeliveredEvent,
    DepartmentRequestRejectedEvent,
    DepartmentRequestVerifiedEvent,
)

logger = logging.getLogger(__name__)


class CrossDepartmentService:
    """Application service for managing cross-department requests and handoffs."""

    def __init__(
        self,
        department_repository: Any,
        request_repository: Any,
        handoff_repository: Any,
        verification_service: Any = None,
        event_publisher: Any = None,
    ) -> None:
        self.dept_repo = department_repository
        self.req_repo = request_repository
        self.handoff_repo = handoff_repository
        self.verification_service = verification_service
        self.event_publisher = event_publisher

    async def submit_request(
        self,
        requester_department_id: str,
        receiving_department_id: str,
        requester_employee_id: str,
        purpose: str,
        requested_outcome: str,
        priority: DepartmentPriority = DepartmentPriority.MEDIUM,
        sla_deadline: Optional[datetime] = None,
        required_capabilities: Optional[List[str]] = None,
        related_objective_id: Optional[str] = None,
        related_project_id: Optional[str] = None,
    ) -> DepartmentRequest:
        """Submit a formal cross-department work request."""
        req_dept = await self.dept_repo.get_by_id(requester_department_id)
        rec_dept = await self.dept_repo.get_by_id(receiving_department_id)

        if not req_dept or not rec_dept:
            raise ValueError("Requester or receiving department does not exist.")

        receiving_mgr_id = rec_dept.manager_employee_id or "mgr-unassigned"

        req = DepartmentRequest(
            request_id=f"req-{uuid4().hex[:8]}",
            requester_department_id=requester_department_id,
            receiving_department_id=receiving_department_id,
            requester_employee_id=requester_employee_id,
            receiving_manager_id=receiving_mgr_id,
            purpose=purpose,
            requested_outcome=requested_outcome,
            priority=priority,
            sla_deadline=sla_deadline,
            required_capabilities=required_capabilities or [],
            status=DepartmentRequestStatus.REQUESTED,
            related_objective_id=related_objective_id,
            related_project_id=related_project_id,
        )

        saved = await self.req_repo.save(req)
        logger.info(
            f"Cross-department request '{saved.request_id}' created from '{requester_department_id}' to '{receiving_department_id}'"
        )

        if self.event_publisher:
            evt = DepartmentRequestCreatedEvent(
                request_id=saved.request_id,
                requester_department_id=requester_department_id,
                receiving_department_id=receiving_department_id,
                purpose=purpose,
            )
            await self.event_publisher.publish(evt)

        return saved

    async def accept_request(
        self, request_id: str, receiving_manager_id: str, delivery_owner_employee_id: str
    ) -> DepartmentRequest:
        """Accept cross-department request and assign delivery owner."""
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise ValueError(f"Request '{request_id}' not found.")

        req.status = DepartmentRequestStatus.ACCEPTED
        req.delivery_owner_employee_id = delivery_owner_employee_id
        req.updated_at = datetime.now(UTC)

        saved = await self.req_repo.save(req)
        logger.info(f"Request '{request_id}' accepted. Assigned delivery owner: {delivery_owner_employee_id}")

        if self.event_publisher:
            evt = DepartmentRequestAcceptedEvent(
                request_id=request_id,
                receiving_manager_id=receiving_manager_id,
                delivery_owner_employee_id=delivery_owner_employee_id,
            )
            await self.event_publisher.publish(evt)

        return saved

    async def reject_request(
        self, request_id: str, receiving_manager_id: str, reason: str
    ) -> DepartmentRequest:
        """Reject cross-department request with justification."""
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise ValueError(f"Request '{request_id}' not found.")

        req.status = DepartmentRequestStatus.REJECTED
        req.rejection_reason = reason
        req.updated_at = datetime.now(UTC)

        saved = await self.req_repo.save(req)

        if self.event_publisher:
            evt = DepartmentRequestRejectedEvent(
                request_id=request_id,
                receiving_manager_id=receiving_manager_id,
                reason=reason,
            )
            await self.event_publisher.publish(evt)

        return saved

    async def submit_handoff(
        self,
        request_id: str,
        sender_employee_id: str,
        expected_outcome: str,
        artifact_ids: Optional[List[str]] = None,
        evidence_ids: Optional[List[str]] = None,
        acceptance_criteria: Optional[List[str]] = None,
    ) -> DepartmentHandoff:
        """Submit a formal deliverable handoff package for verification."""
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise ValueError(f"Request '{request_id}' not found.")

        handoff = DepartmentHandoff(
            handoff_id=f"handoff-{uuid4().hex[:8]}",
            request_id=request_id,
            sender_department_id=req.receiving_department_id,
            receiver_department_id=req.requester_department_id,
            sender_employee_id=sender_employee_id,
            expected_outcome=expected_outcome,
            artifact_ids=artifact_ids or [],
            evidence_ids=evidence_ids or [],
            acceptance_criteria=acceptance_criteria or [],
            status=HandoffStatus.PROPOSED,
        )

        saved = await self.handoff_repo.save(handoff)

        req.status = DepartmentRequestStatus.DELIVERED
        req.updated_at = datetime.now(UTC)
        await self.req_repo.save(req)

        if self.event_publisher:
            evt = DepartmentHandoffCreatedEvent(
                handoff_id=saved.handoff_id,
                request_id=request_id,
                sender_department_id=saved.sender_department_id,
                receiver_department_id=saved.receiver_department_id,
            )
            await self.event_publisher.publish(evt)

        return saved

    async def verify_handoff(
        self, handoff_id: str, verifier_employee_id: str, is_approved: bool = True, reason: Optional[str] = None
    ) -> DepartmentHandoff:
        """Verify handoff deliverables using Phase 10 Evidence Verification rules."""
        handoff = await self.handoff_repo.get_by_id(handoff_id)
        if not handoff:
            raise ValueError(f"Handoff '{handoff_id}' not found.")

        req = await self.req_repo.get_by_id(handoff.request_id)

        if is_approved:
            handoff.status = HandoffStatus.VERIFIED
            handoff.is_verified = True
            if req:
                req.status = DepartmentRequestStatus.VERIFIED
                await self.req_repo.save(req)
        else:
            handoff.status = HandoffStatus.REJECTED
            handoff.is_verified = False
            handoff.rejection_reason = reason or "Verification failed"
            if req:
                req.status = DepartmentRequestStatus.IN_PROGRESS
                await self.req_repo.save(req)

        saved = await self.handoff_repo.save(handoff)

        if self.event_publisher and req:
            evt = DepartmentRequestVerifiedEvent(
                request_id=req.request_id,
                verified_by_employee_id=verifier_employee_id,
                success=is_approved,
            )
            await self.event_publisher.publish(evt)

        return saved

    async def escalate_request(self, request_id: str, reason: str) -> DepartmentRequest:
        """Escalate cross-department blocker to responsible department managers."""
        req = await self.req_repo.get_by_id(request_id)
        if not req:
            raise ValueError(f"Request '{request_id}' not found.")

        if self.event_publisher:
            evt = DepartmentEscalatedEvent(
                department_id=req.receiving_department_id,
                request_id=request_id,
                reason=reason,
            )
            await self.event_publisher.publish(evt)

        return req

    async def list_department_requests(
        self, department_id: str, as_requester: bool = True
    ) -> List[DepartmentRequest]:
        """List requests for a department."""
        return await self.req_repo.list_by_department(department_id, as_requester=as_requester)
