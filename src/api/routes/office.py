"""FastAPI Routes and WebSocket Endpoint for Phase 13 Pixel Office."""

from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.governance_repository import GovernanceRepository
from src.infrastructure.repositories.office_repository import GovernanceOfficeRepository

router = APIRouter(prefix="/office", tags=["Pixel Office"])

global_broadcaster = OfficeRealtimeBroadcaster()


def get_office_projection_service(session: AsyncSession = Depends(get_db_session)) -> OfficeProjectionService:
    emp_repo = SQLAlchemyEmployeeRepository(session)
    gov_repo = GovernanceRepository(session)
    off_repo = GovernanceOfficeRepository(session)
    return OfficeProjectionService(
        employee_repository=emp_repo,
        governance_repository=gov_repo,
        office_repository=off_repo,
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
    repo = GovernanceOfficeRepository(session)
    items = repo.list_human_attention_items()
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
async def office_websocket_endpoint(websocket: WebSocket, client_id: str = "anon-client"):
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
