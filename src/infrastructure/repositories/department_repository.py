"""
SQLAlchemy implementation of DepartmentRepositoryInterface and Phase 14 extensions.
"""

from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.domain.repository import DepartmentRepositoryInterface
from src.infrastructure.models.department_model import (
    DepartmentHandoffModel,
    DepartmentMetricsModel,
    DepartmentModel,
    DepartmentRequestModel,
    DepartmentServiceContractModel,
    department_domain_to_model,
    department_model_to_domain,
)


class SQLAlchemyDepartmentRepository(DepartmentRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, department: Department) -> Department:
        """Save or update a Department entity."""
        model = await self.session.get(DepartmentModel, department.id)
        if model is None:
            model = department_domain_to_model(department)
            self.session.add(model)
        else:
            updated_model = department_domain_to_model(department)
            model.name = updated_model.name
            model.code = updated_model.code
            model.description = updated_model.description
            model.purpose = updated_model.purpose
            model.status = updated_model.status
            model.responsibilities = updated_model.responsibilities
            model.capabilities = updated_model.capabilities
            model.manager_employee_id = updated_model.manager_employee_id
            model.parent_department_id = updated_model.parent_department_id
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at

        await self.session.flush()
        return department_model_to_domain(model)

    async def get_by_id(self, department_id: str) -> Department | None:
        """Find a Department by ID."""
        model = await self.session.get(DepartmentModel, department_id)
        if model is None:
            return None
        return department_model_to_domain(model)

    async def list_all(self) -> list[Department]:
        """List all Department entities."""
        stmt = select(DepartmentModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [department_model_to_domain(m) for m in models]

    # Phase 14 Extensions: Requests
    async def save_request(self, req: DepartmentRequest) -> DepartmentRequest:
        model = await self.session.get(DepartmentRequestModel, req.request_id)
        if model is None:
            model = DepartmentRequestModel(
                request_id=req.request_id,
                requester_department_id=req.requester_department_id,
                receiving_department_id=req.receiving_department_id,
                requester_employee_id=req.requester_employee_id,
                purpose=req.purpose,
                requested_outcome=req.requested_outcome,
                priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
                status=req.status.value if hasattr(req.status, "value") else str(req.status),
                accountable_manager_id=req.accountable_manager_id,
                delivery_owner_employee_id=req.delivery_owner_employee_id,
                target_completion_at=req.target_completion_at,
                required_capabilities=req.required_capabilities,
                related_objective_id=req.related_objective_id,
                related_project_id=req.related_project_id,
                governance_request_id=req.governance_request_id,
                rejection_reason=req.rejection_reason,
                created_at=req.created_at,
                updated_at=req.updated_at,
            )
            self.session.add(model)
        else:
            model.status = req.status.value if hasattr(req.status, "value") else str(req.status)
            model.accountable_manager_id = req.accountable_manager_id
            model.delivery_owner_employee_id = req.delivery_owner_employee_id
            model.rejection_reason = req.rejection_reason
            model.updated_at = req.updated_at

        await self.session.flush()
        return req

    async def get_request(self, request_id: str) -> Optional[DepartmentRequest]:
        model = await self.session.get(DepartmentRequestModel, request_id)
        if model is None:
            return None
        return self._request_model_to_domain(model)

    async def list_requests(
        self,
        department_id: Optional[str] = None,
        as_requester: bool = True,
    ) -> List[DepartmentRequest]:
        stmt = select(DepartmentRequestModel)
        if department_id:
            if as_requester:
                stmt = stmt.where(DepartmentRequestModel.requester_department_id == department_id)
            else:
                stmt = stmt.where(DepartmentRequestModel.receiving_department_id == department_id)

        stmt = stmt.order_by(desc(DepartmentRequestModel.created_at))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._request_model_to_domain(m) for m in models]

    # Handoffs
    async def save_handoff(self, handoff: DepartmentHandoff) -> DepartmentHandoff:
        model = await self.session.get(DepartmentHandoffModel, handoff.handoff_id)
        if model is None:
            model = DepartmentHandoffModel(
                handoff_id=handoff.handoff_id,
                request_id=handoff.request_id,
                sender_department_id=handoff.sender_department_id,
                receiving_department_id=handoff.receiving_department_id,
                sender_employee_id=handoff.sender_employee_id,
                expected_outcome=handoff.expected_outcome,
                receiver_employee_id=handoff.receiver_employee_id,
                artifact_ids=handoff.artifact_ids,
                evidence_summary=handoff.evidence_summary,
                status=handoff.status,
                verification_id=handoff.verification_id,
                accepted_at=handoff.accepted_at,
                created_at=handoff.created_at,
            )
            self.session.add(model)
        else:
            model.status = handoff.status
            model.receiver_employee_id = handoff.receiver_employee_id
            model.verification_id = handoff.verification_id
            model.accepted_at = handoff.accepted_at

        await self.session.flush()
        return handoff

    async def get_handoff(self, handoff_id: str) -> Optional[DepartmentHandoff]:
        model = await self.session.get(DepartmentHandoffModel, handoff_id)
        if model is None:
            return None
        return DepartmentHandoff(
            handoff_id=model.handoff_id,
            request_id=model.request_id,
            sender_department_id=model.sender_department_id,
            receiving_department_id=model.receiving_department_id,
            sender_employee_id=model.sender_employee_id,
            expected_outcome=model.expected_outcome,
            receiver_employee_id=model.receiver_employee_id,
            artifact_ids=list(model.artifact_ids or []),
            evidence_summary=model.evidence_summary,
            status=model.status,
            verification_id=model.verification_id,
            accepted_at=model.accepted_at,
            created_at=model.created_at,
        )

    # Service Contracts
    async def save_service_contract(self, contract: DepartmentServiceContract) -> DepartmentServiceContract:
        model = await self.session.get(DepartmentServiceContractModel, contract.contract_id)
        if model is None:
            model = DepartmentServiceContractModel(
                contract_id=contract.contract_id,
                provider_department_id=contract.provider_department_id,
                consumer_department_id=contract.consumer_department_id,
                service_type=contract.service_type,
                required_input_schema=contract.required_input_schema,
                expected_output_schema=contract.expected_output_schema,
                acceptance_criteria=contract.acceptance_criteria,
                sla_seconds=contract.sla_seconds,
                requires_governance_approval=contract.requires_governance_approval,
                is_active=contract.is_active,
                created_at=contract.created_at,
            )
            self.session.add(model)
        else:
            model.is_active = contract.is_active

        await self.session.flush()
        return contract

    # Metrics
    async def save_metrics(self, metrics: DepartmentMetrics) -> DepartmentMetrics:
        model = await self.session.get(DepartmentMetricsModel, metrics.department_id)
        if model is None:
            model = DepartmentMetricsModel(
                department_id=metrics.department_id,
                active_task_count=metrics.active_task_count,
                completed_task_count=metrics.completed_task_count,
                blocked_task_count=metrics.blocked_task_count,
                incoming_request_count=metrics.incoming_request_count,
                outgoing_request_count=metrics.outgoing_request_count,
                verification_failure_count=metrics.verification_failure_count,
                recovery_attempt_count=metrics.recovery_attempt_count,
                escalation_count=metrics.escalation_count,
                health=metrics.health.value if hasattr(metrics.health, "value") else str(metrics.health),
                updated_at=metrics.updated_at,
            )
            self.session.add(model)
        else:
            model.active_task_count = metrics.active_task_count
            model.completed_task_count = metrics.completed_task_count
            model.blocked_task_count = metrics.blocked_task_count
            model.incoming_request_count = metrics.incoming_request_count
            model.outgoing_request_count = metrics.outgoing_request_count
            model.verification_failure_count = metrics.verification_failure_count
            model.recovery_attempt_count = metrics.recovery_attempt_count
            model.escalation_count = metrics.escalation_count
            model.health = metrics.health.value if hasattr(metrics.health, "value") else str(metrics.health)
            model.updated_at = metrics.updated_at

        await self.session.flush()
        return metrics

    async def get_metrics(self, department_id: str) -> Optional[DepartmentMetrics]:
        model = await self.session.get(DepartmentMetricsModel, department_id)
        if model is None:
            return None
        return DepartmentMetrics(
            department_id=model.department_id,
            active_task_count=model.active_task_count,
            completed_task_count=model.completed_task_count,
            blocked_task_count=model.blocked_task_count,
            incoming_request_count=model.incoming_request_count,
            outgoing_request_count=model.outgoing_request_count,
            verification_failure_count=model.verification_failure_count,
            recovery_attempt_count=model.recovery_attempt_count,
            escalation_count=model.escalation_count,
            health=DepartmentHealth(model.health),
            updated_at=model.updated_at,
        )

    def _request_model_to_domain(self, m: DepartmentRequestModel) -> DepartmentRequest:
        return DepartmentRequest(
            request_id=m.request_id,
            requester_department_id=m.requester_department_id,
            receiving_department_id=m.receiving_department_id,
            requester_employee_id=m.requester_employee_id,
            purpose=m.purpose,
            requested_outcome=m.requested_outcome,
            priority=DepartmentRequestPriority(m.priority),
            status=DepartmentRequestStatus(m.status),
            accountable_manager_id=m.accountable_manager_id,
            delivery_owner_employee_id=m.delivery_owner_employee_id,
            target_completion_at=m.target_completion_at,
            required_capabilities=list(m.required_capabilities or []),
            related_objective_id=m.related_objective_id,
            related_project_id=m.related_project_id,
            governance_request_id=m.governance_request_id,
            rejection_reason=m.rejection_reason,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
