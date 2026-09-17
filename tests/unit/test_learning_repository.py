"""
Unit Tests for Phase 27 Learning Repository & Database Persistence.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.learning_repository import SQLAlchemyLearningRepository
from src.domain.learning import (
    LearningCycle,
    LearningCycleStatus,
    LearningObservation,
    ExpectedVsActualComparison,
    LearningCandidate,
    LearningValidation,
    ImprovementOpportunity,
    AdaptationProposal,
    AdaptationStatus,
    AdaptationType,
    AdaptationRiskLevel,
    AdaptationExecution,
    AdaptationOutcome,
)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as sess:
        yield sess

    await engine.dispose()


@pytest.mark.asyncio
async def test_learning_repository_cycle_and_observation_crud(session: AsyncSession):
    repo = SQLAlchemyLearningRepository(session)
    company_id = "comp-repo-01"

    # Save Learning Cycle
    cycle = LearningCycle(company_id=company_id, purpose="Quarterly Workflow Optimization Audit")
    saved_cycle = await repo.save_learning_cycle(cycle)
    assert saved_cycle.id == cycle.id

    fetched_cycle = await repo.get_learning_cycle_by_id(cycle.id)
    assert fetched_cycle is not None
    assert fetched_cycle.purpose == "Quarterly Workflow Optimization Audit"
    assert fetched_cycle.status == LearningCycleStatus.CREATED

    # Save Observation
    obs = LearningObservation(
        cycle_id=cycle.id,
        company_id=company_id,
        source_subsystem="TASK_ENGINE",
        entity_reference="task-999",
        observed_value={"duration_seconds": 450},
        expected_value={"duration_seconds": 300},
    )
    await repo.save_learning_observation(obs)

    observations = await repo.list_learning_observations_for_cycle(cycle.id)
    assert len(observations) == 1
    assert observations[0].source_subsystem == "TASK_ENGINE"
    assert observations[0].observed_value["duration_seconds"] == 450


@pytest.mark.asyncio
async def test_learning_repository_proposal_and_execution_crud(session: AsyncSession):
    repo = SQLAlchemyLearningRepository(session)
    company_id = "comp-repo-01"

    opp = ImprovementOpportunity(
        company_id=company_id,
        title="Automate Code Review DAG Parallelization",
        affected_area="SOFTWARE_DEVELOPMENT",
        expected_impact="Reduces PR turnaround time by 30%",
    )
    await repo.save_improvement_opportunity(opp)

    proposal = AdaptationProposal(
        company_id=company_id,
        opportunity_id=opp.id,
        adaptation_type=AdaptationType.WORKFLOW_CHANGE,
        risk_level=AdaptationRiskLevel.MEDIUM,
        rationale="Parallelizing static checks accelerates CI pipeline.",
    )
    await repo.save_adaptation_proposal(proposal)

    fetched_prop = await repo.get_adaptation_proposal_by_id(proposal.id)
    assert fetched_prop is not None
    assert fetched_prop.adaptation_type == AdaptationType.WORKFLOW_CHANGE

    execution = AdaptationExecution(
        proposal_id=proposal.id,
        company_id=company_id,
        governance_approval_id="gov-appr-777",
        target_subsystem="TASK_ENGINE",
        execution_payload={"parallel_jobs": 4},
    )
    await repo.save_adaptation_execution(execution)

    fetched_exec = await repo.get_adaptation_execution_by_id(execution.id)
    assert fetched_exec is not None
    assert fetched_exec.governance_approval_id == "gov-appr-777"
