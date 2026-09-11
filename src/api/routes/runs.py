"""
FastAPI Router for AgentRun lifecycle, steps, and checkpoints endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.run_schemas import (
    CheckpointResponse,
    CreateRunRequest,
    RunResponse,
    StepResponse,
)
from src.application.execution_engine import AgentExecutionEngine
from src.domain.exceptions import AgentNotFoundError, AgentValidationError, DomainError
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.checkpoint_repository import SQLAlchemyCheckpointRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository

router = APIRouter(tags=["Runs"])


@router.post(
    "/agents/{agent_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_run(
    agent_id: str,
    req: CreateRunRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RunResponse:
    agent_repo = SQLAlchemyAgentRepository(session)
    run_repo = SQLAlchemyAgentRunRepository(session)
    step_repo = SQLAlchemyExecutionStepRepository(session)
    checkpoint_repo = SQLAlchemyCheckpointRepository(session)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        checkpoint_repo=checkpoint_repo,
    )

    try:
        run = await engine.execute_run(
            agent_id=agent_id,
            objective=req.objective,
            task_id=req.task_id,
            response_schema=req.response_schema,
        )
        return RunResponse.from_domain(run)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AgentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> RunResponse:
    run_repo = SQLAlchemyAgentRunRepository(session)
    run = await run_repo.get_by_id(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found.",
        )
    return RunResponse.from_domain(run)


@router.post("/runs/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> RunResponse:
    agent_repo = SQLAlchemyAgentRepository(session)
    run_repo = SQLAlchemyAgentRunRepository(session)
    step_repo = SQLAlchemyExecutionStepRepository(session)

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
    )

    try:
        run = await engine.cancel_run(run_id)
        return RunResponse.from_domain(run)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/runs/{run_id}/steps", response_model=list[StepResponse])
async def list_run_steps(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> list[StepResponse]:
    step_repo = SQLAlchemyExecutionStepRepository(session)
    steps = await step_repo.list_by_run_id(run_id)
    return [StepResponse.from_domain(s) for s in steps]


@router.get("/runs/{run_id}/checkpoints", response_model=list[CheckpointResponse])
async def list_run_checkpoints(
    run_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> list[CheckpointResponse]:
    checkpoint_repo = SQLAlchemyCheckpointRepository(session)
    checkpoints = await checkpoint_repo.list_by_run_id(run_id)
    return [CheckpointResponse.from_domain(c) for c in checkpoints]
