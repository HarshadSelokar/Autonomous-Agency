"""
Unit tests for EmployeeService (Application Layer).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.employee_service import EmployeeService
from src.domain.agent import Agent, AgentState
from src.domain.department import Department
from src.domain.employee import Employee, EmployeeSkill, EmployeeStatus, SkillProficiency
from src.domain.exceptions import EmployeeNotFoundError, EmployeeValidationError
from src.domain.run import AgentRun, RunStatus


@pytest.fixture
def mock_agent_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = Agent(
        id="agent_001",
        name="Test Agent",
        role="Researcher",
        description="A test agent",
        current_state=AgentState.IDLE,
    )
    return repo


@pytest.fixture
def mock_employee_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    repo.get_by_code.return_value = None
    repo.save.side_effect = lambda emp: emp
    repo.list_all.return_value = []
    return repo


@pytest.fixture
def mock_department_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_id.return_value = Department(
        id="dept_001",
        code="RND",
        name="Research & Development",
    )
    return repo


@pytest.fixture
def mock_execution_engine() -> AsyncMock:
    engine = AsyncMock()
    engine.execute_run.return_value = AgentRun(
        id="run_001",
        agent_id="agent_001",
        objective="Analyze AI Market",
        status=RunStatus.COMPLETED,
    )
    return engine


@pytest.fixture
def service(
    mock_employee_repo: AsyncMock,
    mock_agent_repo: AsyncMock,
    mock_execution_engine: AsyncMock,
    mock_department_repo: AsyncMock,
) -> EmployeeService:
    return EmployeeService(
        employee_repo=mock_employee_repo,
        agent_repo=mock_agent_repo,
        execution_engine=mock_execution_engine,
        department_repo=mock_department_repo,
    )


@pytest.mark.asyncio
async def test_create_employee_success(
    service: EmployeeService, mock_employee_repo: AsyncMock
) -> None:
    emp = Employee(
        id="emp_100",
        employee_code="EMP-100",
        name="Alice Scientist",
        title="Lead Scientist",
        role="scientist",
        agent_id="agent_001",
    )

    created = await service.create_employee(emp)
    assert created.id == "emp_100"
    mock_employee_repo.save.assert_called_once_with(emp)


@pytest.mark.asyncio
async def test_create_employee_duplicate_id_fails(
    service: EmployeeService, mock_employee_repo: AsyncMock
) -> None:
    existing = Employee(
        id="emp_100",
        employee_code="EMP-099",
        name="Existing",
        title="Title",
        role="role",
        agent_id="agent_001",
    )
    mock_employee_repo.get_by_id.return_value = existing

    new_emp = Employee(
        id="emp_100",
        employee_code="EMP-100",
        name="Alice Scientist",
        title="Lead Scientist",
        role="scientist",
        agent_id="agent_001",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await service.create_employee(new_emp)

    assert "already exists" in str(exc.value)


@pytest.mark.asyncio
async def test_create_employee_duplicate_code_fails(
    service: EmployeeService, mock_employee_repo: AsyncMock
) -> None:
    mock_employee_repo.get_by_id.return_value = None
    mock_employee_repo.get_by_code.return_value = MagicMock()

    emp = Employee(
        id="emp_101",
        employee_code="EMP-100",
        name="Bob Dev",
        title="Engineer",
        role="developer",
        agent_id="agent_001",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await service.create_employee(emp)

    assert "is already assigned" in str(exc.value)


@pytest.mark.asyncio
async def test_create_employee_nonexistent_agent_fails(
    service: EmployeeService, mock_agent_repo: AsyncMock
) -> None:
    mock_agent_repo.get_by_id.return_value = None

    emp = Employee(
        id="emp_102",
        employee_code="EMP-102",
        name="Charlie",
        title="Dev",
        role="developer",
        agent_id="agent_missing",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await service.create_employee(emp)

    assert "does not exist in AgentRepository" in str(exc.value)


@pytest.mark.asyncio
async def test_get_employee_not_found(
    service: EmployeeService, mock_employee_repo: AsyncMock
) -> None:
    mock_employee_repo.get_by_id.return_value = None
    with pytest.raises(EmployeeNotFoundError):
        await service.get_employee("missing_id")


@pytest.mark.asyncio
async def test_execute_work_active_employee(
    service: EmployeeService,
    mock_employee_repo: AsyncMock,
    mock_execution_engine: AsyncMock,
) -> None:
    emp = Employee(
        id="emp_active",
        employee_code="EMP-ACT",
        name="Active Worker",
        title="Senior Developer",
        role="developer",
        agent_id="agent_001",
        status=EmployeeStatus.ACTIVE,
        skills=[
            EmployeeSkill(name="python", category="coding", proficiency=SkillProficiency.EXPERT)
        ],
    )
    mock_employee_repo.get_by_id.return_value = emp

    run = await service.execute_work(
        employee_id="emp_active",
        objective="Write unit tests",
    )

    assert run.status == RunStatus.COMPLETED
    mock_execution_engine.execute_run.assert_called_once()
    call_kwargs = mock_execution_engine.execute_run.call_args.kwargs
    assert call_kwargs["agent_id"] == "agent_001"
    assert call_kwargs["objective"] == "Write unit tests"
    assert len(call_kwargs["extra_context_items"]) == 1
    assert "ORGANIZATIONAL EMPLOYEE PROFILE" in call_kwargs["extra_context_items"][0].content


@pytest.mark.asyncio
async def test_execute_work_inactive_employee_raises_error(
    service: EmployeeService, mock_employee_repo: AsyncMock
) -> None:
    emp = Employee(
        id="emp_inactive",
        employee_code="EMP-INA",
        name="Inactive Worker",
        title="Developer",
        role="developer",
        agent_id="agent_001",
        status=EmployeeStatus.INACTIVE,
    )
    mock_employee_repo.get_by_id.return_value = emp

    with pytest.raises(EmployeeValidationError) as exc:
        await service.execute_work(
            employee_id="emp_inactive",
            objective="Do work",
        )

    assert "is not authorized to execute work" in str(exc.value)
