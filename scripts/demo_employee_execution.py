"""
Phase 2 Demonstration Script — Employee Execution & Organizational Delegation.
Demonstrates the full Employee Framework workflow:
YAML Loading -> Department & Agent Binding -> Lifecycle Activation -> Context Injection ->
Agent Runtime Delegation -> Verification & Audit.
"""

import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.agent_loader import load_agent_from_yaml
from src.application.employee_loader import load_employee_from_yaml
from src.application.employee_service import EmployeeService
from src.application.execution_engine import AgentExecutionEngine
from src.application.provider_registry import default_provider_registry
from src.domain.department import Department
from src.domain.employee import EmployeeStatus
from src.infrastructure.config import settings
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.groq_provider import GroqModelProvider
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.run_repository import SQLAlchemyAgentRunRepository
from src.infrastructure.repositories.step_repository import SQLAlchemyExecutionStepRepository


async def run_demo() -> None:
    print("=" * 80)
    print("AUTONOMOUS AI COMPANY PLATFORM - PHASE 2 EMPLOYEE FRAMEWORK DEMO")
    print("=" * 80)

    # 1. Database Setup
    db_url = os.environ.get("DEMO_DATABASE_URL", "sqlite+aiosqlite:///employee_framework_demo.db")
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Provider Registration
    groq_api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        print("[SETUP] Groq API key detected. Using live GroqModelProvider.")
        default_provider_registry.register(GroqModelProvider(api_key=groq_api_key))
    else:
        print("[SETUP] GROQ_API_KEY not configured. Using deterministic FakeModelProvider.")
        default_provider_registry.register(
            FakeModelProvider(
                canned_content=(
                    "RESEARCH REPORT: Multi-Agent Organizational Systems demonstrate superior "
                    "problem solving via specialization, structured communication protocols, "
                    "and clear hierarchy delegation."
                )
            )
        )

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

        # 3. Load & Register Backing Agent
        agent_yaml_path = os.path.join("config", "agents", "researcher.yaml")
        agent = load_agent_from_yaml(agent_yaml_path)
        if not default_provider_registry.has("groq"):
            # Fallback provider override if Groq key is not present
            object.__setattr__(agent.model_configuration, "provider", "fake")
        await agent_repo.save(agent)
        print(f"[AGENT] Saved backing Agent: '{agent.name}' (ID: {agent.id})")

        # 4. Save Department
        dept = Department(
            id="dept_research",
            code="RND",
            name="Research & Development",
            description="Focuses on fundamental AI research and algorithm engineering",
        )
        await department_repo.save(dept)
        print(f"[DEPARTMENT] Saved Department: '{dept.name}' (Code: {dept.code})")

        # 5. Load Employee from YAML definition
        employee_yaml_path = os.path.join("config", "employees", "alice_researcher.yaml")
        emp = load_employee_from_yaml(employee_yaml_path)
        print(f"[LOADER] Loaded Employee definition from '{employee_yaml_path}': {emp.name}")

        created_emp = await service.create_employee(emp)
        print(
            f"[EMPLOYEE] Created Employee '{created_emp.name}' ({created_emp.employee_code}), "
            f"Title: '{created_emp.title}', Initial Status: {created_emp.status.value}"
        )

        # 6. Activate Employee Lifecycle State
        active_emp = await service.change_status(created_emp.id, EmployeeStatus.ACTIVE)
        print(
            f"[LIFECYCLE] Employee '{active_emp.name}' transitioned to "
            f"status: {active_emp.status.value}"
        )

        # 7. Execute Organizational Work
        objective = "Conduct literature review on Multi-Agent Organizational Systems"
        print(f"\n[EXECUTION] Delegating organizational work for '{active_emp.name}'...")
        print(f"            Objective: '{objective}'")

        run = await service.execute_work(
            employee_id=active_emp.id,
            objective=objective,
        )

        print("\n" + "=" * 80)
        print("EXECUTION RESULT")
        print("=" * 80)
        print(f"Run ID:        {run.id}")
        print(f"Agent ID:      {run.agent_id}")
        print(f"Run Status:    {run.status.value}")
        print(f"Tokens Used:   {run.usage.get('total_tokens', 0)}")
        print("\nModel Output:")
        print(run.result.get("content", "") if run.result else "No result returned")

        # 8. List Execution Steps
        steps = await step_repo.list_by_run_id(run.id)
        print("\nExecution Step Trace:")
        for s in steps:
            print(f"  Step {s.step_number}: [{s.step_type.value}] -> {s.status.value}")

    await engine.dispose()
    print("=" * 80)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
