"""Unit tests for DepartmentService."""

from unittest.mock import AsyncMock

import pytest

from src.application.department_service import DepartmentService
from src.domain.department import Department, DepartmentHealth, DepartmentStatus


@pytest.mark.asyncio
async def test_create_department():
    mock_repo = AsyncMock()
    mock_repo.save.side_effect = lambda dept: dept

    service = DepartmentService(department_repository=mock_repo)
    dept = await service.create_department(
        name="Finance",
        code="FIN",
        purpose="Manage budget",
        capabilities=["BUDGETING"],
    )

    assert dept.name == "Finance"
    assert dept.code == "FIN"
    assert dept.status == DepartmentStatus.ACTIVE
    assert "BUDGETING" in dept.capabilities
    mock_repo.save.assert_called_once()


@pytest.mark.asyncio
async def test_update_status():
    mock_repo = AsyncMock()
    existing = Department(id="dept-1", name="Engineering", code="ENG", status=DepartmentStatus.ACTIVE)
    mock_repo.get_by_id.return_value = existing
    mock_repo.save.side_effect = lambda dept: dept

    service = DepartmentService(department_repository=mock_repo)
    updated = await service.update_status("dept-1", DepartmentStatus.PAUSED, reason="Governance pause")

    assert updated.status == DepartmentStatus.PAUSED


@pytest.mark.asyncio
async def test_evaluate_department_health():
    mock_repo = AsyncMock()
    existing = Department(id="dept-qa", name="QA", code="QA", status=DepartmentStatus.ACTIVE)
    mock_repo.get_by_id.return_value = existing

    service = DepartmentService(department_repository=mock_repo)
    report = await service.evaluate_department_health("dept-qa", blocked_tasks_count=5)

    assert report.health == DepartmentHealth.BLOCKED
    assert "High task congestion" in report.reason
