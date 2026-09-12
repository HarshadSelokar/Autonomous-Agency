"""
FastAPI REST API endpoints for Task Engine & Task Scheduler.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.schemas.task_schemas import (
    SchedulerRunRequest,
    SchedulerRunResponse,
    TaskCancelRequest,
    TaskClaimRequest,
    TaskCreateRequest,
    TaskDependencyCreateRequest,
    TaskDependencyResponse,
    TaskResponse,
    TaskReviewRequest,
    TaskReworkRequest,
)
from src.application.dependency_graph_service import DependencyGraphService
from src.application.readiness_evaluator import ReadinessEvaluator
from src.application.task_claim_service import TaskClaimService
from src.application.task_execution_service import TaskExecutionService
from src.application.task_lifecycle_service import TaskLifecycleService
from src.application.task_scheduler_service import TaskSchedulerService
from src.domain.exceptions import (
    DomainError,
    TaskClaimError,
    TaskCycleError,
    TaskDependencyError,
    TaskNotFoundError,
    TaskValidationError,
)
from src.domain.task import Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.infrastructure.database import get_db
from src.infrastructure.repositories.task_dependency_repository import (
    SQLAlchemyTaskDependencyRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository

router = APIRouter(tags=["Task Engine"])


def get_task_services(
    db: Session = Depends(get_db),
) -> tuple[
    SQLAlchemyTaskRepository,
    SQLAlchemyTaskDependencyRepository,
    DependencyGraphService,
    TaskClaimService,
    TaskExecutionService,
    TaskLifecycleService,
    TaskSchedulerService,
]:
    task_repo = SQLAlchemyTaskRepository(db)
    dep_repo = SQLAlchemyTaskDependencyRepository(db)
    graph_service = DependencyGraphService(task_repo, dep_repo)
    claim_service = TaskClaimService(task_repo)
    exec_service = TaskExecutionService(task_repo)
    lifecycle_service = TaskLifecycleService(task_repo, graph_service)
    scheduler_service = TaskSchedulerService(task_repo, claim_service, exec_service)
    return (
        task_repo,
        dep_repo,
        graph_service,
        claim_service,
        exec_service,
        lifecycle_service,
        scheduler_service,
    )


def domain_to_task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        plan_id=task.plan_id,
        title=task.title,
        description=task.description,
        objective_id=task.objective_id,
        work_item_id=task.work_item_id,
        parent_task_id=task.parent_task_id,
        required_capabilities=task.required_capabilities,
        priority=task.priority,
        status=task.status,
        assigned_employee_id=task.assigned_employee_id,
        assignment_id=task.assignment_id,
        execution_run_id=task.execution_run_id,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
        block_reasons=task.block_reasons,
        result=task.result,
        metadata=task.metadata,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def domain_to_dep_response(dep: TaskDependency) -> TaskDependencyResponse:
    return TaskDependencyResponse(
        id=dep.id,
        predecessor_task_id=dep.predecessor_task_id,
        successor_task_id=dep.successor_task_id,
        dependency_type=dep.dependency_type,
        status=dep.status,
        metadata=dep.metadata,
        created_at=dep.created_at,
        updated_at=dep.updated_at,
    )


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreateRequest,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    task_repo, _, graph_service, _, _, _, _ = services
    task_id = f"task-{uuid.uuid4().hex[:8]}"

    try:
        task = Task(
            id=task_id,
            plan_id=body.plan_id,
            title=body.title,
            description=body.description,
            objective_id=body.objective_id,
            work_item_id=body.work_item_id,
            parent_task_id=body.parent_task_id,
            required_capabilities=body.required_capabilities,
            priority=body.priority,
            metadata=body.metadata,
        )

        # Validate parent hierarchy if parent_task_id is set
        if body.parent_task_id:
            parent = task_repo.get_by_id(body.parent_task_id)
            task_map = {task.id: task, parent.id: parent}
            task.set_parent(body.parent_task_id, task_map=task_map)

        # Transition CREATED -> PLANNED for readiness evaluation
        task.transition_to(TaskStatus.PLANNED)

        # Initial readiness evaluation
        task_repo.save(task)
        evaluator = ReadinessEvaluator()
        graph = graph_service.build_graph_for_plan(body.plan_id)
        if evaluator.update_task_readiness(task, graph):
            task_repo.save(task)

        return domain_to_task_response(task)
    except DomainError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    plan_id: str | None = None,
    task_status: TaskStatus | None = None,
    services: Any = Depends(get_task_services),
) -> list[TaskResponse]:
    task_repo = services[0]
    if plan_id:
        tasks = task_repo.get_by_plan_id(plan_id)
    elif task_status:
        tasks = task_repo.get_by_status(task_status)
    else:
        tasks = task_repo.get_all()

    return [domain_to_task_response(t) for t in tasks]


@router.get("/tasks/ready", response_model=list[TaskResponse])
def get_ready_tasks(
    plan_id: str | None = None,
    services: Any = Depends(get_task_services),
) -> list[TaskResponse]:
    scheduler_service = services[6]
    ready = scheduler_service.get_ready_tasks(plan_id)
    return [domain_to_task_response(t) for t in ready]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    task_repo = services[0]
    try:
        task = task_repo.get_by_id(task_id)
        return domain_to_task_response(task)
    except TaskNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/tasks/{task_id}/dependencies",
    response_model=TaskDependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_dependency(
    task_id: str,
    body: TaskDependencyCreateRequest,
    services: Any = Depends(get_task_services),
) -> TaskDependencyResponse:
    _, _, graph_service, _, _, _, _ = services
    dep_id = f"dep-{uuid.uuid4().hex[:8]}"

    try:
        dep = TaskDependency(
            id=dep_id,
            predecessor_task_id=body.predecessor_task_id,
            successor_task_id=body.successor_task_id,
            dependency_type=body.dependency_type,
            metadata=body.metadata,
        )
        saved = await graph_service.add_dependency(dep)
        return domain_to_dep_response(saved)
    except (TaskCycleError, TaskDependencyError, TaskNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.delete(
    "/tasks/{task_id}/dependencies/{dependency_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_dependency(
    task_id: str,
    dependency_id: str,
    services: Any = Depends(get_task_services),
) -> None:
    _, _, graph_service, _, _, _, _ = services
    await graph_service.remove_dependency(dependency_id)


@router.post("/tasks/{task_id}/claim", response_model=TaskResponse)
def claim_task(
    task_id: str,
    body: TaskClaimRequest,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    _, _, _, claim_service, _, _, _ = services
    try:
        claimed = claim_service.claim_task(
            task_id=task_id, worker_id=body.worker_id, metadata=body.metadata
        )
        return domain_to_task_response(claimed)
    except (TaskClaimError, TaskNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/tasks/{task_id}/review", response_model=TaskResponse)
async def review_task(
    task_id: str,
    body: TaskReviewRequest,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    _, _, _, _, _, lifecycle_service, _ = services
    try:
        reviewed = await lifecycle_service.review_task(
            task_id=task_id,
            approved=body.approved,
            reviewer_id=body.reviewer_id,
            feedback=body.feedback,
        )
        return domain_to_task_response(reviewed)
    except (TaskValidationError, TaskNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/tasks/{task_id}/rework", response_model=TaskResponse)
async def rework_task(
    task_id: str,
    body: TaskReworkRequest,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    _, _, _, _, _, lifecycle_service, _ = services
    try:
        reworked = await lifecycle_service.review_task(
            task_id=task_id,
            approved=False,
            reviewer_id=body.reviewer_id,
            feedback=body.feedback,
        )
        return domain_to_task_response(reworked)
    except (TaskValidationError, TaskNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: str,
    force: bool = False,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    _, _, _, _, _, lifecycle_service, _ = services
    try:
        retried = await lifecycle_service.retry_task(task_id=task_id, force=force)
        return domain_to_task_response(retried)
    except (TaskValidationError, TaskNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: str,
    body: TaskCancelRequest,
    services: Any = Depends(get_task_services),
) -> TaskResponse:
    _, _, _, _, _, lifecycle_service, _ = services
    try:
        cancelled = await lifecycle_service.cancel_task(task_id=task_id, reason=body.reason)
        return domain_to_task_response(cancelled)
    except (TaskValidationError, TaskNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/scheduler/run", response_model=SchedulerRunResponse)
async def run_scheduler(
    body: SchedulerRunRequest,
    services: Any = Depends(get_task_services),
) -> SchedulerRunResponse:
    scheduler_service = services[6]
    processed = await scheduler_service.run_scheduler_cycle(
        worker_id=body.worker_id, max_tasks=body.max_tasks
    )
    responses = [domain_to_task_response(t) for t in processed]
    return SchedulerRunResponse(processed_tasks=responses, count=len(responses))
