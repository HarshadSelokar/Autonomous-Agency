"""
Phase 2 Demonstration Script — Employee Governance, Guardrails & State Resilience.
Demonstrates:
1. Inactive / Suspended execution rejection guardrail.
2. Self-manager assignment prevention.
3. Missing agent reference validation.
4. State machine illegal transition prevention.
"""

import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.employee_service import EmployeeService
from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import default_provider_registry
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


async def run_resilience_demo() -> None:
    print("=" * 80)
    print("AUTONOMOUS AI COMPANY PLATFORM - PHASE 2 GOVERNANCE & RESILIENCE DEMO")
    print("=" * 80)

    db_url = os.environ.get("DEMO_DATABASE_URL", "sqlite+aiosqlite:///employee_resilience_demo.db")
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    default_provider_registry.register(FakeModelProvider())

    async with session_factory() as session:
        agent_repo = SQLAlchemyAgentRepository(session)
        employee_repo = SQLAlchemyEmployeeRepository(session)
        department_repo = SQLAlchemyDepartmentRepository(session)
        run_repo = SQLAlchemyAgentRunRepository(session)
        step_repo = SQLAlchemyExecutionStepRepository(session)

        execution_engine = AgentExecutionEngine(
            agent_repo=agent_repo,
            run_repo=run_repo,
            step_repo=step_repo,
            provider_registry=default_provider_registry,
        )

        service = EmployeeService(
            employee_repo=employee_repo,
            agent_repo=agent_repo,
            execution_engine=execution_engine,
            department_repo=department_repo,
        )

        # Save base agent
        agent = Agent(
            id="agent_resilient_01",
            name="Resilient Agent",
            role="Worker",
            model_configuration=ModelConfiguration(provider="fake", model="fake-model"),
        )
        await agent_repo.save(agent)

        print("\n--- DEMO 1: Inactive Employee Execution Guardrail ---")
        emp = Employee(
            id="emp_inactive_demo",
            employee_code="EMP-GUARD-01",
            name="Bob Guarded",
            title="Junior Dev",
            role="developer",
            agent_id="agent_resilient_01",
            status=EmployeeStatus.INACTIVE,
        )
        await service.create_employee(emp)
        print(f"Created Employee '{emp.name}' with status '{emp.status.value}'.")

        try:
            await service.execute_work("emp_inactive_demo", "Perform unauthorized task")
        except EmployeeValidationError as e:
            print(f"[REJECTED AS EXPECTED] {e}")

        print("\n--- DEMO 2: Invalid State Transition Guardrail ---")
        await service.change_status("emp_inactive_demo", EmployeeStatus.ACTIVE)
        print(f"Activated Employee '{emp.name}'.")

        await service.change_status("emp_inactive_demo", EmployeeStatus.TERMINATED)
        print(f"Terminated Employee '{emp.name}'.")

        try:
            await service.change_status("emp_inactive_demo", EmployeeStatus.ACTIVE)
        except InvalidStateTransitionError as e:
            print(f"[REJECTED AS EXPECTED] {e}")

        print("\n--- DEMO 3: Self-Manager Assignment Guardrail ---")
        try:
            Employee(
                id="emp_self_mgr_demo",
                employee_code="EMP-GUARD-02",
                name="Self Manager",
                title="Manager",
                role="manager",
                agent_id="agent_resilient_01",
                manager_id="emp_self_mgr_demo",
            )
        except EmployeeValidationError as e:
            print(f"[REJECTED AS EXPECTED] {e}")

        print("\n--- DEMO 4: Non-Existent Agent Reference Guardrail ---")
        emp_bad_agent = Employee(
            id="emp_no_agent_demo",
            employee_code="EMP-GUARD-03",
            name="Orphan Employee",
            title="Dev",
            role="developer",
            agent_id="agent_missing_99",
        )
        try:
            await service.create_employee(emp_bad_agent)
        except EmployeeValidationError as e:
            print(f"[REJECTED AS EXPECTED] {e}")

    await engine.dispose()
    print("\n" + "=" * 80)
    print("RESILIENCE DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_resilience_demo())
