"""FastAPI Router for Phase 15 Dynamic Team APIs."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.workforce import (
    AddTeamMemberSchema,
    CreateTeamSchema,
    TeamMemberResponseSchema,
    TeamResponseSchema,
)
from src.application.team_formation_service import TeamFormationService
from src.domain.team import TeamType
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.repositories.team_repository import SQLAlchemyTeamRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository

router = APIRouter(prefix="/teams", tags=["Teams"])


def get_team_service(session: AsyncSession = Depends(get_db_session)) -> TeamFormationService:
    team_repo = SQLAlchemyTeamRepository(session)
    wf_repo = SQLAlchemyWorkforceRepository(session)
    emp_repo = SQLAlchemyEmployeeRepository(session)
    outbox_repo = SQLAlchemyOutboxRepository(session)
    return TeamFormationService(
        team_repo=team_repo,
        workforce_repo=wf_repo,
        employee_repo=emp_repo,
        outbox_repo=outbox_repo,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TeamResponseSchema)
async def create_team(
    payload: CreateTeamSchema,
    service: TeamFormationService = Depends(get_team_service),
) -> TeamResponseSchema:
    try:
        ttype = TeamType(payload.team_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid team_type '{payload.team_type}'")

    try:
        team = await service.propose_team(
            name=payload.name,
            code=payload.code,
            purpose=payload.purpose,
            team_type=ttype,
            project_id=payload.project_id,
            department_ids=payload.department_ids,
            manager_id=payload.manager_id,
            creation_reason=payload.creation_reason,
        )
        return _map_team(team)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("", response_model=list[TeamResponseSchema])
async def list_teams(
    service: TeamFormationService = Depends(get_team_service),
) -> list[TeamResponseSchema]:
    teams = await service.team_repo.list_all()
    return [_map_team(t) for t in teams]


@router.get("/{team_id}", response_model=TeamResponseSchema)
async def get_team(
    team_id: str,
    service: TeamFormationService = Depends(get_team_service),
) -> TeamResponseSchema:
    team = await service.team_repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_id}' not found")
    return _map_team(team)


@router.post("/{team_id}/members", response_model=TeamResponseSchema)
async def add_team_member(
    team_id: str,
    payload: AddTeamMemberSchema,
    session: AsyncSession = Depends(get_db_session),
    service: TeamFormationService = Depends(get_team_service),
) -> TeamResponseSchema:
    team = await service.team_repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_id}' not found")

    emp_repo = SQLAlchemyEmployeeRepository(session)
    emp = await emp_repo.get_by_id(payload.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee '{payload.employee_id}' not found")

    try:
        updated_team = await service.form_team(
            team_id=team_id,
            member_employees=[(emp, payload.role_in_team, payload.allocation_percentage)],
        )
        return _map_team(updated_team)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/{team_id}/dissolve", response_model=TeamResponseSchema)
async def dissolve_team(
    team_id: str,
    reason: str = "Project completed",
    service: TeamFormationService = Depends(get_team_service),
) -> TeamResponseSchema:
    try:
        dissolved = await service.dissolve_team(team_id=team_id, reason=reason)
        return _map_team(dissolved)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


def _map_team(t) -> TeamResponseSchema:
    members_schema = [
        TeamMemberResponseSchema(
            id=m.id,
            team_id=m.team_id,
            employee_id=m.employee_id,
            role_in_team=m.role_in_team,
            allocation_percentage=m.allocation_percentage,
            assigned_at=m.assigned_at.isoformat(),
            removed_at=m.removed_at.isoformat() if m.removed_at else None,
        )
        for m in t.members
    ]
    return TeamResponseSchema(
        id=t.id,
        name=t.name,
        code=t.code,
        purpose=t.purpose,
        team_type=t.team_type.value if hasattr(t.team_type, "value") else str(t.team_type),
        project_id=t.project_id,
        department_ids=t.department_ids,
        manager_id=t.manager_id,
        status=t.status.value if hasattr(t.status, "value") else str(t.status),
        capabilities=t.capabilities,
        creation_reason=t.creation_reason,
        created_at=t.created_at.isoformat(),
        dissolved_at=t.dissolved_at.isoformat() if t.dissolved_at else None,
        members=members_schema,
    )
