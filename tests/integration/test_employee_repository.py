"""
Integration tests for Employee and Department repositories persistence using async SQLAlchemy.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.agent import Agent
from src.domain.department import Department
from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository


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
async def test_department_repository_crud(async_session: AsyncSession) -> None:
    dept_repo = SQLAlchemyDepartmentRepository(async_session)

    dept = Department(
        id="dept_eng",
        name="Engineering Department",
        code="ENG",
        description="Core software engineering department",
    )

    saved = await dept_repo.save(dept)
    assert saved.id == "dept_eng"

    fetched = await dept_repo.get_by_id("dept_eng")
    assert fetched is not None
    assert fetched.name == "Engineering Department"

    all_depts = await dept_repo.list_all()
    assert len(all_depts) == 1


@pytest.mark.asyncio
async def test_employee_repository_save_and_get(async_session: AsyncSession) -> None:
    agent_repo = SQLAlchemyAgentRepository(async_session)
    dept_repo = SQLAlchemyDepartmentRepository(async_session)
    emp_repo = SQLAlchemyEmployeeRepository(async_session)

    # Save dependent Agent & Department
    agent = Agent(id="ag_emp1", name="Agent One", role="Worker")
    await agent_repo.save(agent)

    dept = Department(id="dept_res", name="Research", code="RES")
    await dept_repo.save(dept)

    # Manager Employee
    mgr = Employee(
        id="emp_mgr",
        employee_code="EMP-000",
        name="Lead Manager",
        title="Engineering Manager",
        role="manager",
        agent_id="ag_emp1",
        status=EmployeeStatus.ACTIVE,
    )
    await emp_repo.save(mgr)

    # Employee reporting to Manager
    emp = Employee(
        id="emp_100",
        employee_code="EMP-100",
        name="Alice Scientist",
        title="Data Scientist",
        role="data_scientist",
        agent_id="ag_emp1",
        department_id="dept_res",
        manager_id="emp_mgr",
        responsibilities=["Analyze data models"],
        skills=[
            EmployeeSkill(name="python", category="coding", proficiency=SkillProficiency.EXPERT),
        ],
        capabilities=[
            EmployeeCapability(name="data_analysis", description="Statistical modeling"),
        ],
        status=EmployeeStatus.ACTIVE,
    )

    await emp_repo.save(emp)

    fetched = await emp_repo.get_by_id("emp_100")
    assert fetched is not None
    assert fetched.name == "Alice Scientist"
    assert fetched.manager_id == "emp_mgr"
    assert fetched.department_id == "dept_res"
    assert fetched.skills[0].name == "python"
    assert fetched.capabilities[0].name == "data_analysis"

    # Query by code
    by_code = await emp_repo.get_by_code("EMP-100")
    assert by_code is not None
    assert by_code.id == "emp_100"

    # Query by department
    dept_emps = await emp_repo.list_by_department_id("dept_res")
    assert len(dept_emps) == 1
    assert dept_emps[0].id == "emp_100"
