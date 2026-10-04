"""
FastAPI router for Control Plane API (Phase 41).

The control-plane services use the synchronous Session API, so they run through
run_with_sync_session; their state (audit chain, resilience policy, outbox) is stored in
the database rather than in this process.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.auth import Principal, ensure_tenant_access, get_principal
from src.application.audit_governance_v2 import AuditGovernanceV2Service
from src.application.budget_governance_service import BudgetGovernanceService
from src.application.control_plane import ControlPlane
from src.application.event_bus_v2 import EventBusV2
from src.application.resilience_v2_engine import ResilienceV2Engine
from src.application.workflow_engine_v2 import WorkflowEngineV2
from src.domain.exceptions import ResourceBudgetExceededError
from src.infrastructure.database import get_db, run_with_sync_session
from src.infrastructure.models.tenant_model import TenantModel
from src.infrastructure.repositories.budget_repository import SQLAlchemyBudgetRepository
from src.infrastructure.repositories.v2_repository import V2Repository

router = APIRouter(prefix="/control-plane", tags=["Control Plane"])


class ControlPlaneExecuteRequest(BaseModel):
    action: str
    task_data: dict[str, Any] = {}


def _control_plane(session: Session) -> ControlPlane:
    repository = V2Repository(session)
    return ControlPlane(
        workflow_engine=WorkflowEngineV2(repository),
        event_bus=EventBusV2(repository),
        resilience_engine=ResilienceV2Engine(repository),
        audit_service=AuditGovernanceV2Service(repository),
    )


def _require_tenant(session: Session, tenant_id: str) -> TenantModel:
    tenant = session.get(TenantModel, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Tenant '{tenant_id}' was not found.")
    return tenant


@router.get("/overview/{tenant_id}")
async def get_control_plane_overview(
    tenant_id: str,
    db: Any = Depends(get_db),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, Any]:
    ensure_tenant_access(principal, tenant_id)

    def operation(session: Session) -> dict[str, Any]:
        tenant = _require_tenant(session, tenant_id)
        plane = _control_plane(session)
        policy = plane.resilience_engine.get_policy(tenant_id)
        session.commit()
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "tenant_status": tenant.status,
            "audit_trail_count": len(plane.audit_service.get_audit_trail(tenant_id)),
            "audit_chain_intact": plane.audit_service.verify_audit_chain(tenant_id),
            "resilience_policy": {
                "max_retries": policy.max_retries,
                "circuit_breaker_threshold": policy.circuit_breaker_threshold,
                "auto_self_healing": policy.auto_self_healing,
            },
        }

    return await run_with_sync_session(db, operation)


@router.post("/execute")
async def execute_control_plane_request(
    body: ControlPlaneExecuteRequest,
    request: Request,
    db: Any = Depends(get_db),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, Any]:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No tenant is selected for this request.")
    ensure_tenant_access(principal, tenant_id)
    actor_id = principal.user_id if principal else request.headers.get("X-User-ID", "anonymous")

    await run_with_sync_session(db, lambda session: _require_tenant(session, tenant_id))

    # Reserve the declared cost against the tenant's budget before anything is recorded
    estimated_cost = float(body.task_data.get("estimated_cost") or 0)
    if estimated_cost > 0 and hasattr(db, "run_sync"):
        try:
            await BudgetGovernanceService(SQLAlchemyBudgetRepository(db)).reserve_budget(
                tenant_id=tenant_id, amount=estimated_cost
            )
        except ResourceBudgetExceededError as exc:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(exc)) from exc

    def operation(session: Session) -> dict[str, Any]:
        result = _control_plane(session).execute_tenant_request(
            tenant_id=tenant_id, actor_id=actor_id, action=body.action, task_data=body.task_data
        )
        session.commit()
        result["execution_trace"]["budget_reserved"] = estimated_cost
        return result

    try:
        return await run_with_sync_session(db, operation)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
