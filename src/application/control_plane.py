"""
ControlPlane Orchestrator (Phase 41 - Unified Autonomous Operations Control Plane).
Unifies all Phase 32-40 subsystems into a single cohesive multi-tenant platform runtime.
"""

from typing import Any
from src.application.tenant_service import TenantService
from src.application.authorization_service import AuthorizationService
from src.application.tenant_workforce_service import TenantWorkforceService
from src.application.budget_governance_service import BudgetGovernanceService
from src.application.model_router import ModelRouter
from src.application.workflow_engine_v2 import WorkflowEngineV2
from src.application.event_bus_v2 import EventBusV2
from src.application.resilience_v2_engine import ResilienceV2Engine
from src.application.audit_governance_v2 import AuditGovernanceV2Service
from src.domain.audit_v2 import AuditActionType
from src.domain.event_v2 import EventV2


class ControlPlane:
    def __init__(
        self,
        tenant_service: TenantService | None = None,
        auth_service: AuthorizationService | None = None,
        workforce_service: TenantWorkforceService | None = None,
        budget_service: BudgetGovernanceService | None = None,
        model_router: ModelRouter | None = None,
        workflow_engine: WorkflowEngineV2 | None = None,
        event_bus: EventBusV2 | None = None,
        resilience_engine: ResilienceV2Engine | None = None,
        audit_service: AuditGovernanceV2Service | None = None,
    ):
        self.tenant_service = tenant_service or TenantService()
        self.auth_service = auth_service or AuthorizationService()
        self.workforce_service = workforce_service or TenantWorkforceService()
        self.budget_service = budget_service or BudgetGovernanceService()
        self.model_router = model_router or ModelRouter()
        self.workflow_engine = workflow_engine or WorkflowEngineV2()
        self.event_bus = event_bus or EventBusV2()
        self.resilience_engine = resilience_engine or ResilienceV2Engine()
        self.audit_service = audit_service or AuditGovernanceV2Service()

    async def get_tenant_overview(self, tenant_id: str) -> dict[str, Any]:
        tenant = None
        if self.tenant_service.tenant_repo:
            try:
                tenant = await self.tenant_service.get_tenant(tenant_id)
            except Exception:
                pass

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name if tenant else "Tenant " + tenant_id,
            "tenant_status": tenant.status.value if tenant else "ACTIVE",
            "active_workforce": len(self.workforce_service._employees.get(tenant_id, [])),
            "audit_trail_count": len(self.audit_service.get_audit_trail(tenant_id)),
            "resilience_policy": self.resilience_engine.get_policy(tenant_id),
        }

    def execute_tenant_request(
        self,
        tenant_id: str,
        actor_id: str,
        action: str,
        task_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Records a tenant request on the control plane: audit entry, model selection, event.

        When the services were built with a repository the audit record is stored and the
        event goes to the transactional outbox for the worker to publish. Budget reservation
        is done by the API route before this is called.
        """
        # 1. Audit start
        self.audit_service.record_action(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type=AuditActionType.TENANT_ACCESS,
            resource=action,
            details=task_data or {},
        )

        # 2. Model selection for task
        model_decision = self.model_router.select_model_v2(
            tenant_id=tenant_id,
            task_type="general",
        )

        selected_model_name = (
            model_decision.get("primary_model")
            if isinstance(model_decision, dict)
            else getattr(model_decision, "selected_model_id", "default-model")
        )

        # 3. Publish execution event
        event = EventV2(
            tenant_id=tenant_id,
            event_type="control_plane.request.executed",
            payload={"action": action, "model": selected_model_name},
        )
        self.event_bus.publish(event)
        if self.event_bus.repository:
            self.event_bus.publish_outbox(tenant_id, event.event_type, event.payload)

        return {
            "status": "SUCCESS",
            "tenant_id": tenant_id,
            "action": action,
            "selected_model": selected_model_name,
            "execution_trace": {
                "audit_logged": True,
                "event_published": True,
            },
        }
