"""Concurrency tests for Phase 16 Autonomous Company Operations.

Tests single active cycle enforcement and concurrent proposal creation across isolated sessions.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.company_observation_service import CompanyObservationService
from src.application.company_operating_cycle_service import CompanyOperatingCycleService
from src.application.strategic_intelligence_service import StrategicIntelligenceService
from src.domain.company import AutonomousCompany, CompanyStatus
from src.domain.strategy import StrategyProposalType
from src.infrastructure.database import Base
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_operating_cycle_prevention(db_engine):
    """Ensures max 1 active operating cycle per company invariant."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        repo = SQLAlchemyCompanyRepository(session)
        comp = AutonomousCompany(id="comp-conc-1", name="Conc Corp", code="CONC", status=CompanyStatus.ACTIVE)
        await repo.save_company(comp)

        obs_svc = CompanyObservationService(repo)
        strat_svc = StrategicIntelligenceService(repo)
        cycle_svc = CompanyOperatingCycleService(repo, obs_svc, strat_svc)

        cycle1 = await cycle_svc.start_new_cycle(comp.id)
        assert cycle1.cycle_number == 1

        with pytest.raises(ValueError, match="already has an active operating cycle"):
            await cycle_svc.start_new_cycle(comp.id)


@pytest.mark.asyncio
async def test_concurrent_strategy_proposals(db_engine):
    """Ensures concurrent proposal submissions across sessions are saved safely."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        repo = SQLAlchemyCompanyRepository(session)
        comp = AutonomousCompany(id="comp-conc-2", name="Multi Proposal Corp", code="MULTIPROP", status=CompanyStatus.ACTIVE)
        await repo.save_company(comp)

    async def make_proposal(idx: int):
        async with session_factory() as session:
            repo = SQLAlchemyCompanyRepository(session)
            strat_svc = StrategicIntelligenceService(repo)
            prop = await strat_svc.create_strategy_proposal(
                company_id="comp-conc-2",
                proposal_type=StrategyProposalType.ORGANIZATIONAL_EVOLUTION,
                title=f"Concurrent Proposal #{idx}",
                proposal_body=f"Proposal body {idx}",
                reason=f"Reason {idx}",
            )
            await session.commit()
            return prop

    proposals = await asyncio.gather(*(make_proposal(i) for i in range(5)))
    assert len(proposals) == 5

    async with session_factory() as session:
        repo = SQLAlchemyCompanyRepository(session)
        all_props = await repo.list_proposals_for_company("comp-conc-2")
        assert len(all_props) == 5
