"""FastAPI Routes and WebSocket Endpoint for Phase 13 Pixel Office."""

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import AuthenticationFailed, principal_from_credentials
from src.infrastructure.config import settings

from src.api.schemas.office import (
    HumanAttentionItemSchema,
    OfficeActivityItemSchema,
    OfficeCompanyOverviewSchema,
    WorkstationProjectionSchema,
)
from src.application.office_projection_service import OfficeProjectionService
from src.application.office_realtime_service import (
    OfficeRealtimeBroadcaster,
    PixelOfficeConnection,
)
from src.infrastructure.database import SyncRepositoryBridge, get_db_session, run_with_sync_session
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.governance_repository import GovernanceRepository
from src.infrastructure.repositories.office_repository import GovernanceOfficeRepository

from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository
from src.infrastructure.repositories.research_repository import SQLAlchemyResearchRepository

router = APIRouter(prefix="/office", tags=["Pixel Office"])

global_broadcaster = OfficeRealtimeBroadcaster()


def get_office_projection_service(session: AsyncSession = Depends(get_db_session)) -> OfficeProjectionService:
    emp_repo = SQLAlchemyEmployeeRepository(session)
    # Both repositories use the synchronous Session API
    gov_repo = SyncRepositoryBridge(GovernanceRepository, session)
    off_repo = SyncRepositoryBridge(GovernanceOfficeRepository, session)
    k_repo = SQLAlchemyKnowledgeRepository(session)
    r_repo = SQLAlchemyResearchRepository(session)
    return OfficeProjectionService(
        employee_repository=emp_repo,
        governance_repository=gov_repo,
        office_repository=off_repo,
        knowledge_repository=k_repo,
        research_repository=r_repo,
    )


@router.get("/overview", response_model=OfficeCompanyOverviewSchema)
async def get_company_overview(
    service: OfficeProjectionService = Depends(get_office_projection_service),
) -> OfficeCompanyOverviewSchema:
    overview = await service.build_company_overview()
    return OfficeCompanyOverviewSchema(
        company_name=overview.company_name,
        is_emergency_stopped=overview.is_emergency_stopped,
        active_employees_count=overview.active_employees_count,
        working_employees_count=overview.working_employees_count,
        in_meeting_employees_count=overview.in_meeting_employees_count,
        blocked_tasks_count=overview.blocked_tasks_count,
        pending_approvals_count=overview.pending_approvals_count,
        active_projects_count=overview.active_projects_count,
        failed_verifications_count=overview.failed_verifications_count,
        active_recoveries_count=overview.active_recoveries_count,
        candidate_knowledge_count=overview.candidate_knowledge_count,
        validated_knowledge_count=overview.validated_knowledge_count,
        authoritative_knowledge_count=overview.authoritative_knowledge_count,
        contested_knowledge_count=overview.contested_knowledge_count,
        stale_knowledge_count=overview.stale_knowledge_count,
        active_experiments_count=overview.active_experiments_count,
        active_research_programs_count=overview.active_research_programs_count,
        pending_research_requests_count=overview.pending_research_requests_count,
        research_discoveries_count=overview.research_discoveries_count,
        innovation_proposals_count=overview.innovation_proposals_count,
        attention_items=[
            HumanAttentionItemSchema(
                item_id=item.item_id,
                attention_type=item.attention_type.value if hasattr(item.attention_type, "value") else str(item.attention_type),
                title=item.title,
                description=item.description,
                entity_id=item.entity_id,
                entity_type=item.entity_type,
                severity=item.severity,
                action_url=item.action_url,
                created_at=str(item.created_at),
            )
            for item in overview.attention_items
        ],
        recent_activities=[
            OfficeActivityItemSchema(
                activity_id=act.activity_id,
                title=act.title,
                description=act.description,
                category=act.category,
                actor_id=act.actor_id,
                entity_id=act.entity_id,
                timestamp=str(act.timestamp),
            )
            for act in overview.recent_activities
        ],
        updated_at=str(overview.updated_at),
    )


@router.get("/employees", response_model=list[WorkstationProjectionSchema])
async def list_workstations(
    service: OfficeProjectionService = Depends(get_office_projection_service),
) -> list[WorkstationProjectionSchema]:
    overview = await service.build_company_overview()
    workstations: list[WorkstationProjectionSchema] = []
    for dept in overview.departments:
        for ws in dept.workstations:
            workstations.append(
                WorkstationProjectionSchema(
                    employee_id=ws.employee_id,
                    employee_name=ws.employee_name,
                    employee_title=ws.employee_title,
                    role=ws.role,
                    department_id=ws.department_id,
                    manager_id=ws.manager_id,
                    desk_id=ws.desk_id,
                    area_type=ws.area_type.value if hasattr(ws.area_type, "value") else str(ws.area_type),
                    visual_state=ws.visual_state.value if hasattr(ws.visual_state, "value") else str(ws.visual_state),
                    current_task_id=ws.current_task_id,
                    current_task_title=ws.current_task_title,
                    current_project_id=ws.current_project_id,
                    current_project_name=ws.current_project_name,
                    current_activity_summary=ws.current_activity_summary,
                    active_agent_id=ws.active_agent_id,
                    active_tool_name=ws.active_tool_name,
                    active_model_id=ws.active_model_id,
                    is_manager=ws.is_manager,
                    updated_at=str(ws.updated_at),
                )
            )
    return workstations


@router.get("/attention", response_model=list[HumanAttentionItemSchema])
async def list_attention_queue(
    session: AsyncSession = Depends(get_db_session),
) -> list[HumanAttentionItemSchema]:
    items = await run_with_sync_session(
        session, lambda sync_session: GovernanceOfficeRepository(sync_session).list_human_attention_items()
    )
    return [
        HumanAttentionItemSchema(
            item_id=item.item_id,
            attention_type=item.attention_type.value if hasattr(item.attention_type, "value") else str(item.attention_type),
            title=item.title,
            description=item.description,
            entity_id=item.entity_id,
            entity_type=item.entity_type,
            severity=item.severity,
            action_url=item.action_url,
            created_at=str(item.created_at),
        )
        for item in items
    ]


@router.get("/reconcile")
async def reconcile_state(
    service: OfficeProjectionService = Depends(get_office_projection_service),
) -> dict[str, str]:
    """Force backend state reconciliation stream for clients."""
    await service.build_company_overview()
    return {"status": "RECONCILED", "message": "Pixel Office state reconciled with authoritative Company OS"}


@router.websocket("/ws")
async def office_websocket_endpoint(
    websocket: WebSocket, client_id: str = "anon-client", token: str | None = None
):
    # HTTP middleware does not see WebSocket handshakes, so credentials are checked here.
    # Browsers cannot set headers on a WebSocket, hence the ?token= query parameter.
    if settings.AUTH_REQUIRED:
        try:
            principal = principal_from_credentials(
                bearer_token=token, api_key=websocket.headers.get("X-API-Key")
            )
        except AuthenticationFailed:
            principal = None
        if principal is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    await websocket.accept()
    conn = PixelOfficeConnection(
        connection_id=client_id,
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        websocket=websocket,
    )
    global_broadcaster.register_connection(conn)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        global_broadcaster.unregister_connection(client_id)
