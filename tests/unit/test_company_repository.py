"""
Unit tests for Phase 25 Multi-Company & Simulation persistence repository.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.company import (
    Company,
    CompanyLifecycle,
    CompanyType,
    CompanyProfile,
    CompanyMembership,
    CompanyRole,
    CompanyTemplate,
    CompanyRelationship,
    RelationshipType,
    CompanyResourceQuota,
    ExecutionEnvironment,
)
from src.domain.simulation import (
    CompanySimulation,
    SimulationStatus,
    SimulationScenario,
    SimulationSnapshot,
)
from src.infrastructure.database import Base
import src.infrastructure.models.company_model
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_company_crud_operations(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)

    company = Company(
        name="Aegis Autonomous Systems",
        slug="aegis-systems",
        company_type=CompanyType.AUTONOMOUS,
        industry="AEROSPACE",
        lifecycle=CompanyLifecycle.PROPOSED,
    )

    saved = await repo.save_company(company)
    assert saved.id == company.id
    assert saved.slug == "aegis-systems"

    fetched = await repo.get_company_by_slug("aegis-systems")
    assert fetched is not None
    assert fetched.name == "Aegis Autonomous Systems"

    fetched.transition_lifecycle(CompanyLifecycle.INITIALIZING)
    fetched.transition_lifecycle(CompanyLifecycle.ACTIVE)
    updated = await repo.save_company(fetched)
    assert updated.lifecycle == CompanyLifecycle.ACTIVE

    all_companies = await repo.list_companies()
    assert len(all_companies) == 1
    assert all_companies[0].id == company.id


@pytest.mark.asyncio
async def test_company_template_and_membership_repository(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)

    tmpl = CompanyTemplate(
        name="Software Enterprise Template",
        description="Standard engineering company layout",
        industry="SOFTWARE",
        default_departments=["Engineering", "Product", "Sales"],
    )
    saved_tmpl = await repo.save_template(tmpl)
    assert saved_tmpl.name == tmpl.name

    mem = CompanyMembership(
        company_id="comp-101",
        user_id="user-alice",
        role=CompanyRole.ADMIN,
    )
    saved_mem = await repo.save_membership(mem)
    assert saved_mem.role == CompanyRole.ADMIN

    user_mems = await repo.list_memberships_for_user("user-alice")
    assert len(user_mems) == 1
    assert user_mems[0].company_id == "comp-101"


@pytest.mark.asyncio
async def test_company_simulation_and_scenario_repository(async_session: AsyncSession):
    repo = SQLAlchemyMultiCompanyRepository(async_session)

    scenario = SimulationScenario(
        company_id="comp-101",
        name="Hiring Expansion 50%",
        variables={"workforce_multiplier": 1.5, "marketing_boost_pct": 20.0},
    )
    saved_scenario = await repo.save_simulation_scenario(scenario)

    snapshot = SimulationSnapshot(
        company_id="comp-101",
        snapshot_name="Baseline Q3",
        snapshot_data={"revenue_cents": 1000000, "headcount": 10},
    )
    saved_snapshot = await repo.save_simulation_snapshot(snapshot)

    sim = CompanySimulation(
        company_id="comp-101",
        name="Growth Scenario Test",
        scenario_id=saved_scenario.id,
        snapshot_id=saved_snapshot.id,
        environment=ExecutionEnvironment.SIMULATION,
        status=SimulationStatus.READY,
    )
    saved_sim = await repo.save_simulation(sim)
    assert saved_sim.status == SimulationStatus.READY

    sims = await repo.list_simulations_for_company("comp-101")
    assert len(sims) == 1
    assert sims[0].name == "Growth Scenario Test"
