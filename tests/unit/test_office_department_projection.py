"""Unit tests for Phase 14 department extension of Pixel Office projections."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.domain.department import Department, DepartmentStatus
from src.domain.office import EmployeeVisualState, OfficeCompanyProjection
from src.application.office_projection_service import OfficeProjectionService


@pytest.mark.asyncio
async def test_office_projection_with_enterprise_departments():
    mock_emp_repo = AsyncMock()
    mock_dept_repo = AsyncMock()

    emp1 = MagicMock(
        id="emp-1",
        name="Alice Dev",
        department_id="dept-eng",
        department_name="Engineering",
        title="Senior Developer",
        role="DEVELOPER",
        status="ACTIVE",
    )
    emp2 = MagicMock(
        id="emp-2",
        name="Bob Mktg",
        department_id="dept-mktg",
        department_name="Marketing",
        title="Marketing Specialist",
        role="MARKETER",
        status="ACTIVE",
    )
    mock_emp_repo.list_all.return_value = [emp1, emp2]

    service = OfficeProjectionService(
        employee_repository=mock_emp_repo,
        department_repository=mock_dept_repo,
    )

    overview = await service.build_company_overview()
    assert overview.active_employees_count == 2
    assert len(overview.departments) == 2
    dept_names = [d.name for d in overview.departments]
    assert "Engineering" in dept_names
    assert "Marketing" in dept_names
