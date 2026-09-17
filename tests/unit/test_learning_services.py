"""
Unit Tests for Phase 27 Learning Application Services.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
from src.infrastructure.repositories.learning_repository import SQLAlchemyLearningRepository
from src.application.learning_cycle_service import LearningCycleService
from src.application.outcome_comparison_service import OutcomeComparisonService
from src.application.adaptation_proposal_service import AdaptationProposalService
from src.application.controlled_experiment_service import ControlledExperimentService
from src.application.learning_context_builder import LearningContextBuilder
from src.domain.learning import LearningCycleStatus, AdaptationStatus, AdaptationType
from src.domain.exceptions import UnauthorizedAdaptationExecutionError, AdaptationRollbackError


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
async def test_learning_cycle_service_full_flow(session: AsyncSession):
    repo = SQLAlchemyLearningRepository(session)
    service = LearningCycleService(repo)
    company_id = "comp-svc-01"

    # Start Cycle
    cycle = await service.start_learning_cycle(company_id=company_id, purpose="Quarterly Learning Run")
    assert cycle.status == LearningCycleStatus.CREATED

    # Ingest Observation
    obs = await service.ingest_observation(
        cycle_id=cycle.id,
        company_id=company_id,
        source_subsystem="TASK_ENGINE",
        entity_reference="task-101",
        observed_value={"latency_ms": 1200},
        expected_value={"latency_ms": 400},
    )
    assert obs.cycle_id == cycle.id

    # Detect Patterns
    patterns = await service.detect_patterns(cycle_id=cycle.id, company_id=company_id)
    assert len(patterns) > 0

    # Generate Candidate
    candidate = await service.generate_learning_candidate(
        cycle_id=cycle.id,
        company_id=company_id,
        statement="Task latency increases when queue length exceeds 5 items.",
    )
    assert candidate.confidence == 0.60

    # Validate Candidate
    validation = await service.validate_candidate(candidate_id=candidate.id, company_id=company_id, is_valid=True)
    assert validation.is_valid is True

    # Re-fetch candidate to check updated confidence
    updated_cand = await repo.get_learning_candidate_by_id(candidate.id)
    assert updated_cand.confidence == 0.90


@pytest.mark.asyncio
async def test_adaptation_proposal_and_experiment_services(session: AsyncSession):
    repo = SQLAlchemyLearningRepository(session)
    prop_svc = AdaptationProposalService(repo)
    exp_svc = ControlledExperimentService(repo)
    company_id = "comp-svc-01"

    opp = await prop_svc.identify_improvement_opportunity(
        company_id=company_id,
        title="Increase Queue Worker Concurrency",
        affected_area="TASK_ENGINE",
        expected_impact="Reduces task latency by 50%",
    )

    proposal = await prop_svc.propose_adaptation(
        company_id=company_id,
        opportunity_id=opp.id,
        adaptation_type=AdaptationType.WORKFLOW_CHANGE,
    )
    assert proposal.status == AdaptationStatus.PROPOSED

    # Dispatch experiment without governance approval -> MUST FAIL
    with pytest.raises(UnauthorizedAdaptationExecutionError):
        await exp_svc.dispatch_experiment(
            proposal_id=proposal.id,
            company_id=company_id,
            actor_id="AUTO_AGENT",
            governance_approval_id="",
        )

    # Attach governance approval and dispatch -> MUST SUCCEED
    await prop_svc.attach_governance_approval(
        proposal_id=proposal.id, company_id=company_id, governance_approval_id="gov-appr-999"
    )

    execution = await exp_svc.dispatch_experiment(
        proposal_id=proposal.id,
        company_id=company_id,
        actor_id="CHAIRMAN",
        governance_approval_id="gov-appr-999",
    )
    assert execution.governance_approval_id == "gov-appr-999"

    # Evaluate experiment outcome
    outcome = await exp_svc.evaluate_experiment_outcome(
        execution_id=execution.id,
        company_id=company_id,
        expected_metrics={"latency_ms": 400},
        actual_metrics={"latency_ms": 380},
    )
    assert outcome.has_regression is False

    # Adopt adaptation
    adopted = await exp_svc.adopt_adaptation(proposal_id=proposal.id, company_id=company_id)
    assert adopted.status == AdaptationStatus.ADOPTED


@pytest.mark.asyncio
async def test_learning_context_builder(session: AsyncSession):
    repo = SQLAlchemyLearningRepository(session)
    cycle_svc = LearningCycleService(repo)
    builder = LearningContextBuilder(repo)
    company_id = "comp-svc-01"

    cycle = await cycle_svc.start_learning_cycle(company_id=company_id, purpose="Context Test Cycle")
    cand = await cycle_svc.generate_learning_candidate(
        cycle_id=cycle.id,
        company_id=company_id,
        statement="Parallel DAG execution reduces sprint completion time by 25%.",
    )
    await cycle_svc.validate_candidate(candidate_id=cand.id, company_id=company_id, is_valid=True)

    context_str = await builder.build_learning_context(company_id=company_id)
    assert "=== BEGIN ORGANIZATIONAL LEARNING CONTEXT ===" in context_str
    assert "Parallel DAG execution reduces sprint completion time by 25%." in context_str
    assert "=== END ORGANIZATIONAL LEARNING CONTEXT ===" in context_str
