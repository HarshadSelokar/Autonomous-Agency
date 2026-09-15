"""Integration tests for Workforce & Team repositories."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.team import Team, TeamStatus, TeamType
from src.domain.workforce import (
    CapabilityGap,
    CapacitySnapshot,
    EmployeeTemplate,
    GapSeverity,
    StaffingPlanStatus,
    StaffingRecommendation,
    WorkforceAllocation,
    WorkforceChangeRequest,
    WorkforceChangeRequestType,
    WorkforceDecision,
    WorkforceDemand,
    WorkforcePlan,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.team_repository import SQLAlchemyTeamRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository


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
async def test_workforce_repository_crud(db_session):
    repo = SQLAlchemyWorkforceRepository(db_session)

    # 1. Workforce Demand
    demand = WorkforceDemand(
        source_type="PROJECT",
        source_id="proj-100",
        capability="BACKEND_DEVELOPMENT",
        required_count=2,
    )
    saved_demand = await repo.save_demand(demand)
    assert saved_demand.id == demand.id

    fetched_demand = await repo.get_demand(demand.id)
    assert fetched_demand is not None
    assert fetched_demand.capability == "BACKEND_DEVELOPMENT"

    # 2. Capacity Snapshot
    snap = CapacitySnapshot(
        employee_id="emp-alice",
        capability="BACKEND_DEVELOPMENT",
        max_capacity=1.0,
        allocated_capacity=0.5,
    )
    await repo.save_capacity_snapshot(snap)
    snaps = await repo.get_capacity_by_employee("emp-alice")
    assert len(snaps) == 1
    assert snaps[0].allocated_capacity == 0.5

    # 3. Capability Gap
    gap = CapabilityGap(
        capability="SECURITY",
        required_count=3,
        available_count=1,
        gap_count=2,
        severity=GapSeverity.HIGH,
    )
    await repo.save_capability_gap(gap)
    gaps = await repo.list_capability_gaps()
    assert len(gaps) == 1
    assert gaps[0].capability == "SECURITY"

    # 4. Staffing Recommendation
    rec = StaffingRecommendation(
        demand_id=demand.id,
        candidate_employee_ids=["emp-alice", "emp-bob"],
        final_score=0.85,
        reasoning="Good capacity match",
    )
    await repo.save_recommendation(rec)
    fetched_rec = await repo.get_recommendation(rec.id)
    assert fetched_rec is not None
    assert fetched_rec.candidate_employee_ids == ["emp-alice", "emp-bob"]

    # 5. Workforce Change Request
    chg = WorkforceChangeRequest(
        request_type=WorkforceChangeRequestType.FORM_TEAM,
        target_id="team-phoenix",
        requested_by_id="mgr-john",
        justification="Project Phoenix requirements",
    )
    await repo.save_change_request(chg)
    reqs = await repo.list_change_requests()
    assert len(reqs) == 1
    assert reqs[0].target_id == "team-phoenix"


@pytest.mark.asyncio
async def test_team_repository_crud(db_session):
    repo = SQLAlchemyTeamRepository(db_session)

    team = Team(
        name="Security Guild",
        code="SEC",
        purpose="Platform Security Review",
        team_type=TeamType.CROSS_DEPARTMENT,
        project_id="proj-sec",
    )
    team.activate()
    team.add_member("emp-alice", role_in_team="LEAD")
    team.add_member("emp-bob", role_in_team="MEMBER")

    saved_team = await repo.save(team)
    assert saved_team.code == "SEC"
    assert len(saved_team.members) == 2

    fetched_team = await repo.get_by_id(team.id)
    assert fetched_team is not None
    assert fetched_team.status == TeamStatus.ACTIVE
    assert len(fetched_team.members) == 2

    emp_teams = await repo.list_by_employee("emp-alice")
    assert len(emp_teams) == 1
    assert emp_teams[0].id == team.id
