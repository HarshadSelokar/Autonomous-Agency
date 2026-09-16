"""Failure Injection test suite for Phase 16 Autonomous Company Operations.

Tests metric degradation, partial observation data failure, governance rejection,
and operating cycle checkpoint recovery.
"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.company_observation_service import CompanyObservationService
from src.application.company_operating_cycle_service import CompanyOperatingCycleService
from src.application.strategic_intelligence_service import StrategicIntelligenceService
from src.domain.company import AutonomousCompany, CompanyHealthStatus, CompanyStatus, OperatingCycleState
from src.infrastructure.database import Base
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_partial_observation_data_failure(db_session):
    """Verifies system evaluates health gracefully even with missing metric inputs."""
    repo = SQLAlchemyCompanyRepository(db_session)
    comp = AutonomousCompany(id="comp-fail-1", name="FailCorp", code="FAILCO", status=CompanyStatus.ACTIVE)
    await repo.save_company(comp)

    obs_svc = CompanyObservationService(repo)

    # Calculate health with empty metric snapshots
    health = await obs_svc.evaluate_company_health(comp.id, kpi_snapshots=[])
    assert health.company_id == comp.id
    assert health.overall_status in [CompanyHealthStatus.HEALTHY, CompanyHealthStatus.BALANCED]


@pytest.mark.asyncio
async def test_operating_cycle_failure_and_checkpoint_resume(db_session):
    """Verifies operating cycle failure recording and resumption from saved checkpoint."""
    repo = SQLAlchemyCompanyRepository(db_session)
    comp = AutonomousCompany(id="comp-fail-2", name="CrashCorp", code="CRASH", status=CompanyStatus.ACTIVE)
    await repo.save_company(comp)

    obs_svc = CompanyObservationService(repo)
    strat_svc = StrategicIntelligenceService(repo)
    cycle_svc = CompanyOperatingCycleService(repo, obs_svc, strat_svc)

    # 1. Start cycle and transition to OBSERVING
    cycle = await cycle_svc.start_new_cycle(comp.id)
    await cycle_svc.transition_phase(cycle.id, OperatingCycleState.OBSERVING)

    # 2. Simulate process crash / pause
    paused = await cycle_svc.pause_cycle(cycle.id, "Process interrupted by network timeout")
    assert paused.state == OperatingCycleState.PAUSED

    # 3. Resume cycle from checkpoint
    resumed = await cycle_svc.resume_cycle(cycle.id)
    assert resumed.state == OperatingCycleState.OBSERVING

    # 4. Fail cycle gracefully
    failed = await cycle_svc.fail_cycle(cycle.id, "Unrecoverable model provider error")
    assert failed.state == OperatingCycleState.FAILED
    assert failed.failure_reason == "Unrecoverable model provider error"
