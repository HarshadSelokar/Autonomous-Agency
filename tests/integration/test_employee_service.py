"""
Integration tests for EmployeeService with real SQLite repositories and AgentExecutionEngine.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application.employee_service import EmployeeService
from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import ModelProviderRegistry
from src.domain.agent import Agent, ModelConfiguration
from src.domain.department import Department
from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.domain.exceptions import EmployeeValidationError
from src.domain.run import RunStatus
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


@pytest.mark.asyncio
async def test_employee_service_full_lifecycle_and_execution(
    async_session: AsyncSession,
) -> None:
    # 1. Repositories setup
    agent_repo = SQLAlchemyAgentRepository(async_session)
    employee_repo = SQLAlchemyEmployeeRepository(async_session)
    department_repo = SQLAlchemyDepartmentRepository(async_session)
    run_repo = SQLAlchemyAgentRunRepository(async_session)
    step_repo = SQLAlchemyExecutionStepRepository(async_session)

    # 2. Fake Model Provider setup
    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider(
        canned_content=(
            "Report on AI Agents: AI Agents demonstrate high efficiency in workflow execution."
        )
    )
    registry.register(fake_provider)

    # 3. Execution Engine & Employee Service
    engine = AgentExecutionEngine(
        agent_repo=agent_repo,
        run_repo=run_repo,
        step_repo=step_repo,
        provider_registry=registry,
    )
    service = EmployeeService(
        employee_repo=employee_repo,
        agent_repo=agent_repo,
        execution_engine=engine,
        department_repo=department_repo,
    )

    # 4. Save underlying Agent & Department
    agent = Agent(
        id="agent_researcher_01",
        name="Alice Agent",
        role="Researcher",
        model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
    )
    await agent_repo.save(agent)

    dept = Department(
        id="dept_research",
        code="RND",
        name="Research & Development",
    )
    await department_repo.save(dept)

    # 5. Create Employee via Service
    emp = Employee(
        id="emp_alice",
        employee_code="EMP-101",
        name="Alice Smith",
        title="Lead AI Researcher",
        role="researcher",
        agent_id="agent_researcher_01",
        department_id="dept_research",
        status=EmployeeStatus.INACTIVE,
        skills=[
            EmployeeSkill(
                name="python", category="programming", proficiency=SkillProficiency.EXPERT
            )
        ],
        capabilities=[
            EmployeeCapability(name="deep_research", description="Conduct deep research")
        ],
        responsibilities=["Conduct technical research", "Publish findings"],
    )

    created_emp = await service.create_employee(emp)
    assert created_emp.id == "emp_alice"
    assert created_emp.status == EmployeeStatus.INACTIVE

    # 6. Verify INACTIVE employee cannot execute work
    with pytest.raises(EmployeeValidationError) as exc:
        await service.execute_work(
            employee_id="emp_alice",
            objective="Research LLM agents",
        )
    assert "is in status 'INACTIVE' and is not authorized to execute work" in str(exc.value)

    # 7. Activate Employee
    activated_emp = await service.change_status("emp_alice", EmployeeStatus.ACTIVE)
    assert activated_emp.status == EmployeeStatus.ACTIVE

    # 8. Execute work successfully
    run = await service.execute_work(
        employee_id="emp_alice",
        objective="Research LLM agents",
    )

    assert run.status == RunStatus.COMPLETED
    assert run.result is not None
    assert "AI Agents demonstrate high efficiency" in run.result["content"]

    # 9. Verify run was logged in run_repo
    stored_run = await run_repo.get_by_id(run.id)
    assert stored_run is not None
    assert stored_run.agent_id == "agent_researcher_01"
    assert stored_run.status == RunStatus.COMPLETED
