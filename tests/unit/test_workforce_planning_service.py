"""Unit tests for WorkforcePlanningService."""

from unittest.mock import AsyncMock

import pytest

from src.application.workforce_planning_service import WorkforcePlanningService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.workforce import (
    CapacitySnapshot,
    GapSeverity,
    WorkforceDemand,
)


@pytest.fixture
def mock_workforce_repo():
    repo = AsyncMock()
    repo.save_demand = AsyncMock(side_effect=lambda d: d)
    repo.save_capacity_snapshot = AsyncMock(side_effect=lambda s: s)
    repo.save_capability_gap = AsyncMock(side_effect=lambda g: g)
    repo.save_recommendation = AsyncMock(side_effect=lambda r: r)
    repo.save_plan = AsyncMock(side_effect=lambda p: p)
    repo.list_demands = AsyncMock(return_value=[])
    repo.list_capacity_snapshots = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def sample_employees():
    e1 = Employee(
        id="emp-alice",
        employee_code="EMP-001",
        name="Alice",
        title="Senior Backend Engineer",
        role="ENGINEER",
        agent_id="agent-1",
        status=EmployeeStatus.ACTIVE,
        capabilities=["BACKEND_DEVELOPMENT", "SECURITY"],
    )
    e2 = Employee(
        id="emp-bob",
        employee_code="EMP-002",
        name="Bob",
        title="Frontend Engineer",
        role="ENGINEER",
        agent_id="agent-2",
        status=EmployeeStatus.ACTIVE,
        capabilities=["FRONTEND_DEVELOPMENT"],
    )
    return [e1, e2]


@pytest.mark.asyncio
async def test_create_workforce_demand(mock_workforce_repo):
    service = WorkforcePlanningService(mock_workforce_repo)
    demand = await service.create_workforce_demand(
        source_type="PROJECT",
        source_id="proj-1",
        capability="BACKEND_DEVELOPMENT",
        required_count=2,
    )
    assert demand.capability == "BACKEND_DEVELOPMENT"
    assert demand.required_count == 2
    mock_workforce_repo.save_demand.assert_called_once()


@pytest.mark.asyncio
async def test_calculate_capacity_snapshots(mock_workforce_repo, sample_employees):
    service = WorkforcePlanningService(mock_workforce_repo)
    active_allocs = {"emp-alice": 40.0, "emp-bob": 100.0}

    snaps = await service.calculate_capacity_snapshots(
        employees=sample_employees,
        active_allocations_by_emp=active_allocs,
    )
    assert len(snaps) == 3  # Alice has 2 caps, Bob has 1 cap
    alice_backend_snap = next(s for s in snaps if s.employee_id == "emp-alice" and s.capability == "BACKEND_DEVELOPMENT")
    assert alice_backend_snap.available_capacity == pytest.approx(0.6)

    bob_snap = next(s for s in snaps if s.employee_id == "emp-bob")
    assert bob_snap.available_capacity == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_detect_capability_gaps(mock_workforce_repo):
    service = WorkforcePlanningService(mock_workforce_repo)

    demands = [
        WorkforceDemand(source_type="PROJECT", source_id="p1", capability="SECURITY", required_count=3, priority=4),
        WorkforceDemand(source_type="PROJECT", source_id="p1", capability="FRONTEND_DEVELOPMENT", required_count=1, priority=2),
    ]
    snapshots = [
        CapacitySnapshot(employee_id="emp-1", capability="SECURITY", available_capacity=1.0),
    ]

    gaps = await service.detect_capability_gaps(demands=demands, snapshots=snapshots)
    assert len(gaps) == 2

    sec_gap = next(g for g in gaps if g.capability == "SECURITY")
    assert sec_gap.required_count == 3
    assert sec_gap.available_count == 1
    assert sec_gap.gap_count == 2
    assert sec_gap.severity in (GapSeverity.HIGH, GapSeverity.CRITICAL)


@pytest.mark.asyncio
async def test_generate_staffing_recommendation(mock_workforce_repo, sample_employees):
    service = WorkforcePlanningService(mock_workforce_repo)

    demand = WorkforceDemand(source_type="PROJECT", source_id="p1", capability="BACKEND_DEVELOPMENT", required_count=1)
    snaps = {"emp-alice": 0.8, "emp-bob": 0.0}
    rel = {"emp-alice": 0.95, "emp-bob": 0.5}

    rec = await service.generate_staffing_recommendation(
        demand=demand,
        all_employees=sample_employees,
        snapshots_by_emp=snaps,
        reliability_scores_by_emp=rel,
    )
    assert rec.demand_id == demand.id
    assert rec.candidate_employee_ids == ["emp-alice"]
    assert rec.final_score > 0.7
    assert "Alice" in rec.reasoning
