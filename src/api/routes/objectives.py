"""
FastAPI Router for Phase 3 Objective & Organizational Orchestration endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.objective_schemas import (
    CreateObjectiveRequest,
    ObjectiveResponse,
    ProvideClarificationRequest,
    RequestClarificationRequest,
)
from src.api.schemas.plan_schemas import (
    AssignmentResponse,
    AssignWorkItemRequest,
    DecisionResponse,
    EscalateWorkItemRequest,
    HandleBlockerRequest,
    PlanResponse,
    ReassignWorkItemRequest,
    SubmitPlanRequest,
    WorkItemResponse,
)
from src.api.schemas.run_schemas import RunResponse
from src.application.execution_engine import AgentExecutionEngine
from src.application.manager_orchestration_service import ManagerOrchestrationService
from src.domain.exceptions import (
    AssignmentError,
    EscalationError,
    ObjectiveNotFoundError,
    ObjectiveValidationError,
    PlanValidationError,
)
from src.domain.plan import Plan
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
from src.infrastructure.repositories.plan_repository import SQLAlchemyPlanRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository
from src.infrastructure.repositories.work_item_repository import SQLAlchemyWorkItemRepository

router = APIRouter(prefix="/objectives", tags=["Objectives & Orchestration"])


def get_manager_orchestration_service(
    session: AsyncSession = Depends(get_db_session),
) -> ManagerOrchestrationService:
    obj_repo = SQLAlchemyObjectiveRepository(session)
    plan_repo = SQLAlchemyPlanRepository(session)
    wi_repo = SQLAlchemyWorkItemRepository(session)
    asgn_repo = SQLAlchemyAssignmentRepository(session)
    dec_repo = SQLAlchemyDecisionRepository(session)
    emp_repo = SQLAlchemyEmployeeRepository(session)
    agent_repo = SQLAlchemyAgentRepository(session)
    run_repo = SQLAlchemyAgentRunRepository(session)
    step_repo = SQLAlchemyExecutionStepRepository(session)
    checkpoint_repo = SQLAlchemyCheckpointRepository(session)

    execution_engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        checkpoint_repo=checkpoint_repo,
    )

    return ManagerOrchestrationService(
        objective_repo=obj_repo,
        plan_repo=plan_repo,
        work_item_repo=wi_repo,
        assignment_repo=asgn_repo,
        decision_repo=dec_repo,
        employee_repo=emp_repo,
        agent_repo=agent_repo,
        execution_engine=execution_engine,
    )


@router.post("", response_model=ObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(
    req: CreateObjectiveRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> ObjectiveResponse:
    try:
        obj = await service.create_objective(
            objective_id=req.id,
            title=req.title,
            description=req.description,
            requester=req.requester,
            priority=req.priority,
            constraints=req.constraints,
            manager_id=req.manager_id,
        )
        return ObjectiveResponse.from_domain(obj)
    except ObjectiveValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{objective_id}", response_model=ObjectiveResponse)
async def get_objective(
    objective_id: str,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> ObjectiveResponse:
    try:
        obj = await service.get_objective(objective_id)
        return ObjectiveResponse.from_domain(obj)
    except ObjectiveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{objective_id}/clarify-request", response_model=ObjectiveResponse)
async def request_clarification(
    objective_id: str,
    req: RequestClarificationRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> ObjectiveResponse:
    try:
        obj = await service.request_clarification(objective_id, req.questions)
        return ObjectiveResponse.from_domain(obj)
    except ObjectiveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{objective_id}/clarify-answers", response_model=ObjectiveResponse)
async def provide_clarification(
    objective_id: str,
    req: ProvideClarificationRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> ObjectiveResponse:
    try:
        obj = await service.provide_clarification(objective_id, req.answers)
        return ObjectiveResponse.from_domain(obj)
    except ObjectiveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{objective_id}/plan",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_plan(
    objective_id: str,
    req: SubmitPlanRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> PlanResponse:
    try:
        work_items = [w.to_domain(req.id) for w in req.work_items]
        plan = Plan(
            id=req.id,
            objective_id=objective_id,
            manager_id=req.manager_id,
            assumptions=req.assumptions,
            goals=req.goals,
            work_items=work_items,
            required_capabilities=req.required_capabilities,
            risks=req.risks,
            constraints=req.constraints,
            metadata=req.metadata,
        )
        saved_plan, _ = await service.submit_and_validate_plan(plan)
        return PlanResponse.from_domain(saved_plan)
    except ObjectiveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (PlanValidationError, ObjectiveValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/plans/{plan_id}/approve", response_model=PlanResponse)
async def approve_plan(
    plan_id: str,
    manager_id: str,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> PlanResponse:
    try:
        approved = await service.approve_plan(plan_id, manager_id)
        return PlanResponse.from_domain(approved)
    except PlanValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/work-items/{work_item_id}/assign",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_work_item(
    work_item_id: str,
    req: AssignWorkItemRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> AssignmentResponse:
    try:
        asgn = await service.assign_work_item(
            work_item_id=work_item_id,
            employee_id=req.employee_id,
            assigned_by_manager_id=req.assigned_by_manager_id,
            reason=req.reason,
        )
        return AssignmentResponse.from_domain(asgn)
    except AssignmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/work-items/{work_item_id}/reassign", response_model=AssignmentResponse)
async def reassign_work_item(
    work_item_id: str,
    req: ReassignWorkItemRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> AssignmentResponse:
    try:
        asgn = await service.reassign_work_item(
            work_item_id=work_item_id,
            new_employee_id=req.new_employee_id,
            assigned_by_manager_id=req.assigned_by_manager_id,
            reason=req.reason,
        )
        return AssignmentResponse.from_domain(asgn)
    except AssignmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{objective_id}/blocker", response_model=WorkItemResponse)
async def handle_blocker(
    objective_id: str,
    req: HandleBlockerRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> WorkItemResponse:
    try:
        wi = await service.handle_blocker(
            work_item_id=req.work_item_id,
            objective_id=objective_id,
            employee_id=req.employee_id,
            reason=req.reason,
        )
        return WorkItemResponse.from_domain(wi)
    except (AssignmentError, ObjectiveNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{objective_id}/escalate", response_model=DecisionResponse)
async def escalate_work_item(
    objective_id: str,
    req: EscalateWorkItemRequest,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> DecisionResponse:
    try:
        dec = await service.escalate_work_item(
            work_item_id=req.work_item_id,
            objective_id=objective_id,
            manager_id=req.manager_id,
            reason=req.reason,
        )
        return DecisionResponse.from_domain(dec)
    except EscalationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{objective_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_manager_objective(
    objective_id: str,
    manager_id: str,
    service: ManagerOrchestrationService = Depends(get_manager_orchestration_service),
) -> RunResponse:
    try:
        run = await service.execute_manager_objective(objective_id, manager_id)
        return RunResponse.from_domain(run)
    except ObjectiveNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ObjectiveValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
