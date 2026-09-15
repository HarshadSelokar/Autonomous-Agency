"""FastAPI Router for Phase 15 Dynamic Workforce APIs."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.workforce import (
    ApproveWorkforceChangeSchema,
    CapabilityGapResponseSchema,
    CreateWorkforceDemandSchema,
    GenerateRecommendationSchema,
    RequestWorkforceChangeSchema,
    StaffingRecommendationResponseSchema,
    WorkforceChangeRequestResponseSchema,
    WorkforceDemandResponseSchema,
    WorkforceHealthResponseSchema,
)
from src.application.team_formation_service import TeamFormationService
from src.application.workforce_planning_service import WorkforcePlanningService
from src.domain.workforce import (
    CapabilityGap,
    StaffingRecommendation,
    WorkforceChangeRequest,
    WorkforceChangeRequestType,
    WorkforceDemand,
)
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.repositories.team_repository import SQLAlchemyTeamRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository

router = APIRouter(prefix="/workforce", tags=["Workforce"])


def get_workforce_service(session: AsyncSession = Depends(get_db_session)) -> WorkforcePlanningService:
    wf_repo = SQLAlchemyWorkforceRepository(session)
    outbox_repo = SQLAlchemyOutboxRepository(session)
    return WorkforcePlanningService(workforce_repo=wf_repo, outbox_repo=outbox_repo)


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


@router.post("/demands", status_code=status.HTTP_201_CREATED, response_model=WorkforceDemandResponseSchema)
async def create_demand(
    payload: CreateWorkforceDemandSchema,
    service: WorkforcePlanningService = Depends(get_workforce_service),
) -> WorkforceDemandResponseSchema:
    demand = await service.create_workforce_demand(
        source_type=payload.source_type,
        source_id=payload.source_id,
        capability=payload.capability,
        required_count=payload.required_count,
        priority=payload.priority,
        department_id=payload.department_id,
        duration_days=payload.duration_days,
        risk_level=payload.risk_level,
        governance_required=payload.governance_required,
    )
    return _map_demand(demand)


@router.get("/demands", response_model=list[WorkforceDemandResponseSchema])
async def list_demands(
    service: WorkforcePlanningService = Depends(get_workforce_service),
) -> list[WorkforceDemandResponseSchema]:
    demands = await service.workforce_repo.list_demands()
    return [_map_demand(d) for d in demands]


@router.get("/gaps", response_model=list[CapabilityGapResponseSchema])
async def list_gaps(
    service: WorkforcePlanningService = Depends(get_workforce_service),
) -> list[CapabilityGapResponseSchema]:
    gaps = await service.detect_capability_gaps()
    return [_map_gap(g) for g in gaps]


@router.post("/recommendations", status_code=status.HTTP_201_CREATED, response_model=StaffingRecommendationResponseSchema)
async def generate_recommendation(
    payload: GenerateRecommendationSchema,
    session: AsyncSession = Depends(get_db_session),
    service: WorkforcePlanningService = Depends(get_workforce_service),
) -> StaffingRecommendationResponseSchema:
    demand = await service.workforce_repo.get_demand(payload.demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail=f"Demand '{payload.demand_id}' not found")

    emp_repo = SQLAlchemyEmployeeRepository(session)
    all_employees = await emp_repo.list_all()

    rec = await service.generate_staffing_recommendation(
        demand=demand,
        all_employees=all_employees,
    )
    return _map_recommendation(rec)


@router.post("/requests", status_code=status.HTTP_201_CREATED, response_model=WorkforceChangeRequestResponseSchema)
async def request_change(
    payload: RequestWorkforceChangeSchema,
    team_service: TeamFormationService = Depends(get_team_service),
) -> WorkforceChangeRequestResponseSchema:
    try:
        req_type = WorkforceChangeRequestType(payload.request_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid request_type '{payload.request_type}'")

    req = await team_service.request_workforce_change(
        request_type=req_type,
        target_id=payload.target_id,
        requested_by_id=payload.requested_by_id,
        justification=payload.justification,
    )
    return _map_request(req)


@router.post("/requests/{request_id}/approve")
async def approve_change(
    request_id: str,
    payload: ApproveWorkforceChangeSchema,
    team_service: TeamFormationService = Depends(get_team_service),
) -> dict[str, str]:
    try:
        decision = await team_service.approve_workforce_change(
            change_request_id=request_id,
            actor_id=payload.actor_id,
            governance_approval_id=payload.governance_approval_id,
            is_human_approval=payload.is_human_approval,
            reason=payload.reason,
        )
        return {"decision_id": decision.id, "status": "APPROVED", "reason": decision.reason}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/health", response_model=WorkforceHealthResponseSchema)
async def get_workforce_health(
    session: AsyncSession = Depends(get_db_session),
    service: WorkforcePlanningService = Depends(get_workforce_service),
) -> WorkforceHealthResponseSchema:
    emp_repo = SQLAlchemyEmployeeRepository(session)
    team_repo = SQLAlchemyTeamRepository(session)

    emps = await emp_repo.list_all()
    teams = await team_repo.list_all()
    gaps = await service.detect_capability_gaps()
    demands = await service.workforce_repo.list_demands()

    active_emps = [e for e in emps if e.is_executable()]
    active_teams = [t for t in teams if t.status.value in ("ACTIVE", "FORMING")]

    health_status = "HEALTHY"
    if gaps:
        health_status = "CAPABILITY_CONSTRAINED"

    return WorkforceHealthResponseSchema(
        status=health_status,
        total_active_employees=len(active_emps),
        active_teams_count=len(active_teams),
        open_capability_gaps=len(gaps),
        unmet_demand_count=len(demands),
        overloaded_employee_count=0,
    )


def _map_demand(d: WorkforceDemand) -> WorkforceDemandResponseSchema:
    return WorkforceDemandResponseSchema(
        id=d.id,
        source_type=d.source_type,
        source_id=d.source_id,
        department_id=d.department_id,
        capability=d.capability,
        required_count=d.required_count,
        priority=d.priority,
        duration_days=d.duration_days,
        deadline=d.deadline.isoformat() if d.deadline else None,
        risk_level=d.risk_level,
        governance_required=d.governance_required,
        created_at=d.created_at.isoformat(),
    )


def _map_gap(g: CapabilityGap) -> CapabilityGapResponseSchema:
    return CapabilityGapResponseSchema(
        id=g.id,
        capability=g.capability,
        required_count=g.required_count,
        available_count=g.available_count,
        gap_count=g.gap_count,
        severity=g.severity.value if hasattr(g.severity, "value") else str(g.severity),
        affected_project_ids=g.affected_project_ids,
        created_at=g.created_at.isoformat(),
    )


def _map_recommendation(r: StaffingRecommendation) -> StaffingRecommendationResponseSchema:
    return StaffingRecommendationResponseSchema(
        id=r.id,
        demand_id=r.demand_id,
        candidate_employee_ids=r.candidate_employee_ids,
        capability_fit_score=r.capability_fit_score,
        availability_score=r.availability_score,
        workload_score=r.workload_score,
        reliability_score=r.reliability_score,
        final_score=r.final_score,
        reasoning=r.reasoning,
        created_at=r.created_at.isoformat(),
    )


def _map_request(req: WorkforceChangeRequest) -> WorkforceChangeRequestResponseSchema:
    return WorkforceChangeRequestResponseSchema(
        id=req.id,
        request_type=req.request_type.value if hasattr(req.request_type, "value") else str(req.request_type),
        target_id=req.target_id,
        requested_by_id=req.requested_by_id,
        justification=req.justification,
        governance_approval_id=req.governance_approval_id,
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        created_at=req.created_at.isoformat(),
        processed_at=req.processed_at.isoformat() if req.processed_at else None,
    )
