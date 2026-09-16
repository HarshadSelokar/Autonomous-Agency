"""
Customer Success & Support Application Service for Phase 24.

Orchestrates onboarding plans, customer health snapshots, support cases,
and engineering task escalations with strict customer context security.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.gtm import (
    Customer,
    CustomerLifecycleState,
    CustomerOnboardingPlan,
    CustomerHealthSnapshot,
    SupportCase,
    SupportCaseStatus,
    SupportPriority,
)
from src.domain.events import (
    CustomerCreatedEvent,
    CustomerOnboardedEvent,
    SupportCaseCreatedEvent,
    SupportCaseResolvedEvent,
    CustomerHealthChangedEvent,
    ChurnSignalDetectedEvent,
)
from src.domain.exceptions import CustomerDataIsolationError
from src.domain.repository import GTMRepositoryInterface


class CustomerSuccessSupportService:
    """Manages onboarding, customer health, support cases, and escalations."""

    def __init__(self, repository: GTMRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    def verify_customer_access(self, requestor_customer_id: str, target_customer_id: str) -> None:
        """Enforces tenant boundary customer data isolation."""
        if requestor_customer_id != target_customer_id:
            raise CustomerDataIsolationError(requestor_customer_id, target_customer_id)

    async def create_customer_from_opportunity(
        self,
        name: str,
        domain: str,
        segment: str = "ENTERPRISE",
        account_manager_id: Optional[str] = None,
    ) -> Customer:
        cust = Customer(
            id=str(uuid.uuid4()),
            name=name,
            domain=domain,
            segment=segment,
            lifecycle_state=CustomerLifecycleState.CUSTOMER,
            account_manager_id=account_manager_id,
            health_score=100.0,
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_customer(cust)
        self._publish_event(CustomerCreatedEvent(customer_id=saved.id, name=saved.name, segment=saved.segment))
        return saved

    async def initiate_onboarding(self, customer_id: str, order_id: Optional[str] = None) -> CustomerOnboardingPlan:
        plan = CustomerOnboardingPlan(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            order_id=order_id,
            milestones_json=[
                {"name": "Kickoff & Account Setup", "status": "COMPLETED"},
                {"name": "System Configuration & Integration", "status": "IN_PROGRESS"},
                {"name": "Team Training & Activation", "status": "PENDING"},
            ],
            status="IN_PROGRESS",
            completion_pct=33.3,
            started_at=datetime.now(UTC),
        )
        # Update customer lifecycle to ONBOARDING
        cust = await self.repository.get_customer_by_id(customer_id)
        if cust:
            cust.lifecycle_state = CustomerLifecycleState.ONBOARDING
            await self.repository.save_customer(cust)

        self._publish_event(CustomerOnboardedEvent(customer_id=customer_id, onboarding_plan_id=plan.id))
        return plan

    async def complete_onboarding(self, customer_id: str) -> Customer:
        cust = await self.repository.get_customer_by_id(customer_id)
        if not cust:
            raise ValueError(f"Customer '{customer_id}' not found.")

        cust.lifecycle_state = CustomerLifecycleState.ACTIVE
        saved = await self.repository.save_customer(cust)
        return saved

    async def create_support_case(
        self,
        customer_id: str,
        subject: str,
        description: str,
        priority: SupportPriority = SupportPriority.MEDIUM,
        assigned_employee_id: Optional[str] = None,
    ) -> SupportCase:
        case = SupportCase(
            id=str(uuid.uuid4()),
            customer_id=customer_id,
            subject=subject,
            description=description,
            priority=priority,
            status=SupportCaseStatus.OPEN,
            assigned_employee_id=assigned_employee_id,
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_support_case(case)
        self._publish_event(
            SupportCaseCreatedEvent(
                case_id=saved.id,
                customer_id=saved.customer_id,
                subject=saved.subject,
                priority=saved.priority.value,
            )
        )
        return saved

    async def escalate_support_case_to_task(self, case_id: str, engineering_task_id: str) -> SupportCase:
        case = await self.repository.get_support_case_id(case_id) if hasattr(self.repository, "get_support_case_id") else await self.repository.get_support_case_by_id(case_id)
        if not case:
            raise ValueError(f"Support case '{case_id}' not found.")

        case.status = SupportCaseStatus.IN_PROGRESS
        case.escalated_task_id = engineering_task_id
        return await self.repository.save_support_case(case)

    async def resolve_support_case(self, case_id: str, resolved_by: str, resolution_notes: str) -> SupportCase:
        case = await self.repository.get_support_case_by_id(case_id)
        if not case:
            raise ValueError(f"Support case '{case_id}' not found.")

        case.status = SupportCaseStatus.RESOLVED
        case.resolution_notes = resolution_notes
        saved = await self.repository.save_support_case(case)

        self._publish_event(
            SupportCaseResolvedEvent(
                case_id=saved.id,
                resolved_by=resolved_by,
                resolution_notes=resolution_notes,
            )
        )
        return saved
