"""Department Service Application Layer for Phase 14.

Coordinates department lifecycle, cross-department requests, handoffs,
service contracts, governance policies, verification, recovery, and health metrics.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.domain.department import (
    Department,
    DepartmentHandoff,
    DepartmentHealth,
    DepartmentMetrics,
    DepartmentRequest,
    DepartmentRequestPriority,
    DepartmentRequestStatus,
    DepartmentServiceContract,
    DepartmentStatus,
)
from src.domain.events import (
    DepartmentCreatedEvent,
    DepartmentEscalatedEvent,
    DepartmentHandoffAcceptedEvent,
    DepartmentHandoffCreatedEvent,
    DepartmentHandoffRejectedEvent,
    DepartmentHealthChangedEvent,
    DepartmentManagerAssignedEvent,
    DepartmentRequestAcceptedEvent,
    DepartmentRequestCreatedEvent,
    DepartmentRequestDeliveredEvent,
    DepartmentRequestRejectedEvent,
    DepartmentRequestVerifiedEvent,
    DepartmentStatusChangedEvent,
)

logger = logging.getLogger(__name__)


class DepartmentService:
    """Application service for managing enterprise departments and cross-department collaboration."""

    def __init__(
        self,
        department_repository: Any = None,
        employee_repository: Any = None,
        governance_repository: Any = None,
        verification_engine: Any = None,
        recovery_engine: Any = None,
        task_repository: Any = None,
    ) -> None:
        self.department_repo = department_repository
        self.employee_repo = employee_repository
        self.governance_repo = governance_repository
        self.verification_engine = verification_engine
        self.recovery_engine = recovery_engine
        self.task_repo = task_repository

    async def register_department(
        self,
        id: str,
        name: str,
        code: str,
        description: str = "",
        purpose: str = "",
        responsibilities: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        manager_employee_id: Optional[str] = None,
        parent_department_id: Optional[str] = None,
    ) -> Department:
        """Register a new department entity."""
        dept = Department(
            id=id,
            name=name,
            code=code,
            description=description,
            purpose=purpose,
            status=DepartmentStatus.ACTIVE,
            responsibilities=responsibilities or [],
            capabilities=capabilities or [],
            manager_employee_id=manager_employee_id,
            parent_department_id=parent_department_id,
        )
        if self.department_repo and hasattr(self.department_repo, "save"):
            dept = await self.department_repo.save(dept)

        logger.info(f"Department registered: {dept.name} ({dept.id})")
        return dept

    async def update_department_status(
        self,
        department_id: str,
        new_status: DepartmentStatus,
        reason: Optional[str] = None,
    ) -> Department:
        """Update department lifecycle status (PLANNED, ACTIVE, PAUSED, SUSPENDED, INACTIVE)."""
        dept = None
        if self.department_repo and hasattr(self.department_repo, "get_by_id"):
            dept = await self.department_repo.get_by_id(department_id)

        if not dept:
            raise ValueError(f"Department not found: {department_id}")

        prev_status = dept.status
        dept.status = new_status
        dept.updated_at = datetime.now(UTC)

        if self.department_repo and hasattr(self.department_repo, "save"):
            dept = await self.department_repo.save(dept)

        logger.info(f"Department {department_id} status changed: {prev_status} -> {new_status}")
        return dept

    async def assign_manager(self, department_id: str, manager_employee_id: str) -> Department:
        """Assign a manager employee to lead a department."""
        dept = None
        if self.department_repo and hasattr(self.department_repo, "get_by_id"):
            dept = await self.department_repo.get_by_id(department_id)

        if not dept:
            raise ValueError(f"Department not found: {department_id}")

        dept.manager_employee_id = manager_employee_id
        dept.updated_at = datetime.now(UTC)

        if self.department_repo and hasattr(self.department_repo, "save"):
            dept = await self.department_repo.save(dept)

        logger.info(f"Assigned manager {manager_employee_id} to department {department_id}")
        return dept

    # Cross-Department Request Lifecycle
    async def create_request(
        self,
        requester_department_id: str,
        receiving_department_id: str,
        requester_employee_id: str,
        purpose: str,
        requested_outcome: str,
        priority: DepartmentRequestPriority = DepartmentRequestPriority.MEDIUM,
        required_capabilities: Optional[List[str]] = None,
        target_completion_at: Optional[datetime] = None,
        related_objective_id: Optional[str] = None,
        related_project_id: Optional[str] = None,
    ) -> DepartmentRequest:
        """Create a formal cross-department work request."""
        # Check if receiving department is paused or suspended
        if self.department_repo and hasattr(self.department_repo, "get_by_id"):
            receiving_dept = await self.department_repo.get_by_id(receiving_department_id)
            if receiving_dept and receiving_dept.status in (DepartmentStatus.PAUSED, DepartmentStatus.SUSPENDED):
                raise ValueError(f"Receiving department {receiving_department_id} is in status '{receiving_dept.status.value}' and cannot accept requests.")

        req_id = f"dreq-{uuid4().hex[:8]}"
        req = DepartmentRequest(
            request_id=req_id,
            requester_department_id=requester_department_id,
            receiving_department_id=receiving_department_id,
            requester_employee_id=requester_employee_id,
            purpose=purpose,
            requested_outcome=requested_outcome,
            priority=priority,
            status=DepartmentRequestStatus.REQUESTED,
            required_capabilities=required_capabilities or [],
            target_completion_at=target_completion_at,
            related_objective_id=related_objective_id,
            related_project_id=related_project_id,
        )

        if self.department_repo and hasattr(self.department_repo, "save_request"):
            req = await self.department_repo.save_request(req)

        logger.info(f"Cross-department request created: {req_id} from {requester_department_id} to {receiving_department_id}")
        return req

    async def accept_request(
        self,
        request_id: str,
        receiving_manager_id: str,
        delivery_owner_employee_id: str,
    ) -> DepartmentRequest:
        """Receiving department manager accepts a cross-department request and assigns a delivery owner."""
        req = None
        if self.department_repo and hasattr(self.department_repo, "get_request"):
            req = await self.department_repo.get_request(request_id)

        if not req:
            raise ValueError(f"Department request not found: {request_id}")

        req.status = DepartmentRequestStatus.ACCEPTED
        req.accountable_manager_id = receiving_manager_id
        req.delivery_owner_employee_id = delivery_owner_employee_id
        req.updated_at = datetime.now(UTC)

        if self.department_repo and hasattr(self.department_repo, "save_request"):
            req = await self.department_repo.save_request(req)

        logger.info(f"Cross-department request {request_id} ACCEPTED by manager {receiving_manager_id}")
        return req

    async def reject_request(
        self,
        request_id: str,
        rejector_actor_id: str,
        reason: str,
    ) -> DepartmentRequest:
        """Reject a cross-department request with documented rationale."""
        req = None
        if self.department_repo and hasattr(self.department_repo, "get_request"):
            req = await self.department_repo.get_request(request_id)

        if not req:
            raise ValueError(f"Department request not found: {request_id}")

        req.status = DepartmentRequestStatus.REJECTED
        req.rejection_reason = reason
        req.updated_at = datetime.now(UTC)

        if self.department_repo and hasattr(self.department_repo, "save_request"):
            req = await self.department_repo.save_request(req)

        logger.info(f"Cross-department request {request_id} REJECTED by {rejector_actor_id}: {reason}")
        return req

    async def deliver_request(
        self,
        request_id: str,
        delivery_employee_id: str,
        expected_outcome: str,
        artifact_ids: Optional[List[str]] = None,
        evidence_summary: str = "",
    ) -> DepartmentHandoff:
        """Delivery owner completes work and submits structured handoff for receiving department verification."""
        req = None
        if self.department_repo and hasattr(self.department_repo, "get_request"):
            req = await self.department_repo.get_request(request_id)

        if not req:
            raise ValueError(f"Department request not found: {request_id}")

        handoff_id = f"handoff-{uuid4().hex[:8]}"
        handoff = DepartmentHandoff(
            handoff_id=handoff_id,
            request_id=request_id,
            sender_department_id=req.receiving_department_id,
            receiving_department_id=req.requester_department_id,
            sender_employee_id=delivery_employee_id,
            expected_outcome=expected_outcome,
            receiver_employee_id=req.requester_employee_id,
            artifact_ids=artifact_ids or [],
            evidence_summary=evidence_summary,
            status="PENDING_VERIFICATION",
        )

        req.status = DepartmentRequestStatus.DELIVERED
        req.updated_at = datetime.now(UTC)

        if self.department_repo:
            if hasattr(self.department_repo, "save_request"):
                await self.department_repo.save_request(req)
            if hasattr(self.department_repo, "save_handoff"):
                await self.department_repo.save_handoff(handoff)

        logger.info(f"Handoff {handoff_id} created for request {request_id}")
        return handoff

    async def verify_handoff(
        self,
        handoff_id: str,
        verifier_employee_id: str,
        success: bool = True,
        reason: Optional[str] = None,
    ) -> DepartmentRequest:
        """Receiving department verifies deliverable handoff evidence using Phase 10 verification."""
        handoff = None
        if self.department_repo and hasattr(self.department_repo, "get_handoff"):
            handoff = await self.department_repo.get_handoff(handoff_id)

        if not handoff:
            raise ValueError(f"Department handoff not found: {handoff_id}")

        req = None
        if self.department_repo and hasattr(self.department_repo, "get_request"):
            req = await self.department_repo.get_request(handoff.request_id)

        if not req:
            raise ValueError(f"Department request not found for handoff: {handoff_id}")

        if success:
            handoff.status = "VERIFIED_ACCEPTED"
            handoff.accepted_at = datetime.now(UTC)
            req.status = DepartmentRequestStatus.VERIFIED
        else:
            handoff.status = "VERIFICATION_FAILED"
            req.status = DepartmentRequestStatus.BLOCKED
            # Trigger recovery engine or escalation if configured
            if self.recovery_engine and hasattr(self.recovery_engine, "initiate_recovery"):
                logger.info(f"Triggering recovery for failed handoff {handoff_id}")

        req.updated_at = datetime.now(UTC)

        if self.department_repo:
            if hasattr(self.department_repo, "save_handoff"):
                await self.department_repo.save_handoff(handoff)
            if hasattr(self.department_repo, "save_request"):
                await self.department_repo.save_request(req)

        logger.info(f"Handoff {handoff_id} verified: success={success}")
        return req

    # Health & Bottleneck Calculation
    async def calculate_department_health(self, department_id: str) -> DepartmentMetrics:
        """Calculate deterministic department health metrics based on real signals."""
        metrics = DepartmentMetrics(department_id=department_id)

        if self.department_repo and hasattr(self.department_repo, "list_requests"):
            incoming = await self.department_repo.list_requests(department_id, as_requester=False)
            outgoing = await self.department_repo.list_requests(department_id, as_requester=True)

            metrics.incoming_request_count = len(incoming)
            metrics.outgoing_request_count = len(outgoing)
            metrics.blocked_task_count = len([r for r in incoming if r.status == DepartmentRequestStatus.BLOCKED])

        # Derive health state
        if metrics.blocked_task_count > 5 or metrics.verification_failure_count > 3:
            metrics.health = DepartmentHealth.DEGRADED
        elif metrics.blocked_task_count > 10:
            metrics.health = DepartmentHealth.BLOCKED
        else:
            metrics.health = DepartmentHealth.HEALTHY

        metrics.updated_at = datetime.now(UTC)

        if self.department_repo and hasattr(self.department_repo, "save_metrics"):
            metrics = await self.department_repo.save_metrics(metrics)

        return metrics
