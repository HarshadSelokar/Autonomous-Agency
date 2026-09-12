"""
Failure-Injection Test Suite covering Phase 2 Employee Framework failure modes & edge cases.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.employee_service import EmployeeService
from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import ModelProviderRegistry
from src.domain.agent import Agent, ModelConfiguration
from src.domain.employee import Employee, EmployeeStatus
from src.domain.exceptions import EmployeeValidationError, InvalidStateTransitionError
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository


@pytest.fixture
async def async_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def employee_service(async_session: AsyncSession) -> EmployeeService:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    employee_repo = SQLAlchemyEmployeeRepository(async_session)
    department_repo = SQLAlchemyDepartmentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    registry = ModelProviderRegistry()
    registry.register(FakeModelProvider())

    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
    )

    # Pre-save standard backing Agent
    agent = Agent(
        id="agent_base_01",
        name="Base Agent",
        role="Worker",
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    await agent_repo.save(agent)

    return EmployeeService(
        employee_repo=employee_repo,
        agent_repo=agent_repo,
        execution_engine=engine,
        department_repo=department_repo,
    )


# 1. Inactive Employee Execution Rejection
@pytest.mark.asyncio
async def test_failure_mode_inactive_employee_execution_rejected(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_inactive",
        employee_code="EMP-FAIL-01",
        name="Inactive Bob",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
        status=EmployeeStatus.INACTIVE,
    )
    await employee_service.create_employee(emp)

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.execute_work("emp_fail_inactive", "Execute task")

    assert "is in status 'INACTIVE' and is not authorized to execute work" in str(exc.value)


# 2. Suspended Employee Execution Rejection
@pytest.mark.asyncio
async def test_failure_mode_suspended_employee_execution_rejected(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_suspended",
        employee_code="EMP-FAIL-02",
        name="Suspended Bob",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
        status=EmployeeStatus.INACTIVE,
    )
    await employee_service.create_employee(emp)
    await employee_service.change_status("emp_fail_suspended", EmployeeStatus.ACTIVE)
    await employee_service.change_status("emp_fail_suspended", EmployeeStatus.SUSPENDED)

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.execute_work("emp_fail_suspended", "Execute task")

    assert "is in status 'SUSPENDED' and is not authorized to execute work" in str(exc.value)


# 3. Terminated Employee Execution Rejection
@pytest.mark.asyncio
async def test_failure_mode_terminated_employee_execution_rejected(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_terminated",
        employee_code="EMP-FAIL-03",
        name="Terminated Bob",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
        status=EmployeeStatus.INACTIVE,
    )
    await employee_service.create_employee(emp)
    await employee_service.change_status("emp_fail_terminated", EmployeeStatus.ACTIVE)
    await employee_service.change_status("emp_fail_terminated", EmployeeStatus.TERMINATED)

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.execute_work("emp_fail_terminated", "Execute task")

    assert "is in status 'TERMINATED' and is not authorized to execute work" in str(exc.value)


# 4. Non-Existent Agent Reference Rejection
@pytest.mark.asyncio
async def test_failure_mode_nonexistent_agent_reference_rejected(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_no_agent",
        employee_code="EMP-FAIL-04",
        name="No Agent Bob",
        title="Dev",
        role="developer",
        agent_id="agent_does_not_exist",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.create_employee(emp)

    assert "Referenced Agent 'agent_does_not_exist' does not exist" in str(exc.value)


# 5. Self Manager Assignment Rejection
@pytest.mark.asyncio
async def test_failure_mode_self_manager_assignment_rejected(
    employee_service: EmployeeService,
) -> None:
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            id="emp_self_mgr",
            employee_code="EMP-FAIL-05",
            name="Self Manager",
            title="Dev",
            role="developer",
            agent_id="agent_base_01",
            manager_id="emp_self_mgr",
        )

    assert "cannot be assigned as their own manager" in str(exc.value)


# 6. Non-Existent Manager Reference Rejection
@pytest.mark.asyncio
async def test_failure_mode_nonexistent_manager_reference_rejected(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_bad_mgr",
        employee_code="EMP-FAIL-06",
        name="Bad Manager Reference",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
        manager_id="mgr_does_not_exist",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.create_employee(emp)

    assert "Referenced Manager 'mgr_does_not_exist' does not exist" in str(exc.value)


# 7. Non-Existent Department Reference Rejection
@pytest.mark.asyncio
async def test_failure_mode_nonexistent_department_reference_rejected(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_bad_dept",
        employee_code="EMP-FAIL-07",
        name="Bad Dept Reference",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
        department_id="dept_does_not_exist",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.create_employee(emp)

    assert "Referenced Department 'dept_does_not_exist' does not exist" in str(exc.value)


# 8. Invalid Lifecycle State Transition
@pytest.mark.asyncio
async def test_failure_mode_invalid_lifecycle_state_transition(
    employee_service: EmployeeService,
) -> None:
    emp = Employee(
        id="emp_fail_transition",
        employee_code="EMP-FAIL-08",
        name="Terminated Transition",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
        status=EmployeeStatus.INACTIVE,
    )
    await employee_service.create_employee(emp)
    await employee_service.change_status("emp_fail_transition", EmployeeStatus.ACTIVE)
    await employee_service.change_status("emp_fail_transition", EmployeeStatus.TERMINATED)

    with pytest.raises(InvalidStateTransitionError) as exc:
        await employee_service.change_status("emp_fail_transition", EmployeeStatus.ACTIVE)

    assert "cannot transition from 'TERMINATED' to 'ACTIVE'" in str(exc.value)


# 9. Duplicate Employee Code Rejection
@pytest.mark.asyncio
async def test_failure_mode_duplicate_employee_code_rejected(
    employee_service: EmployeeService,
) -> None:
    emp1 = Employee(
        id="emp_code_1",
        employee_code="EMP-DUP-CODE",
        name="First Employee",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
    )
    await employee_service.create_employee(emp1)

    emp2 = Employee(
        id="emp_code_2",
        employee_code="EMP-DUP-CODE",
        name="Second Employee",
        title="Dev",
        role="developer",
        agent_id="agent_base_01",
    )

    with pytest.raises(EmployeeValidationError) as exc:
        await employee_service.create_employee(emp2)

    assert "Employee code 'EMP-DUP-CODE' is already assigned" in str(exc.value)
