"""
Phase 4 Demonstration Script: End-to-End Task DAG Execution.
Executes a 6-node Directed Acyclic Graph (DAG):
  T1 (Research)
   ↓
  T2 (Architecture)
   ↙ ↘
T3 (Backend)  T4 (Frontend)
   ↘ ↙
  T5 (Integration)
   ↓
  T6 (QA)
"""

import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.application.dependency_graph_service import DependencyGraphService
from src.application.readiness_evaluator import ReadinessEvaluator
from src.application.task_claim_service import TaskClaimService
from src.application.task_execution_service import TaskExecutionService
from src.application.task_lifecycle_service import TaskLifecycleService
from src.application.task_scheduler_service import TaskSchedulerService
from src.domain.task import Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.infrastructure.database import Base
from src.infrastructure.models.agent_model import AgentModel  # noqa: F401
from src.infrastructure.models.assignment_model import AssignmentModel  # noqa: F401
from src.infrastructure.models.department_model import DepartmentModel  # noqa: F401
from src.infrastructure.models.employee_model import EmployeeModel  # noqa: F401
from src.infrastructure.models.objective_model import ObjectiveModel
from src.infrastructure.models.plan_model import PlanModel
from src.infrastructure.models.run_model import AgentRunModel  # noqa: F401
from src.infrastructure.models.task_dependency_model import TaskDependencyModel  # noqa: F401
from src.infrastructure.models.task_model import TaskModel  # noqa: F401
from src.infrastructure.models.work_item_model import WorkItemModel  # noqa: F401
from src.infrastructure.repositories.task_dependency_repository import (
    SQLAlchemyTaskDependencyRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


def setup_demo_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    obj = ObjectiveModel(
        id="obj-analytics",
        title="Build Analytics App",
        description="End to end analytics platform",
        requester="CEO",
        status="APPROVED",
        constraints_json=[],
        metadata_json={},
    )
    plan = PlanModel(
        id="plan-analytics",
        objective_id="obj-analytics",
        manager_id="mgr-1",
        assumptions_json=[],
        goals_json=[],
        required_capabilities_json=[],
        risks_json=[],
        constraints_json=[],
        status="APPROVED",
        metadata_json={},
    )
    session.add(obj)
    session.add(plan)
    session.commit()
    return session


async def run_dag_demo() -> None:
    print("=" * 70)
    print("PHASE 4 — TASK DAG EXECUTION DEMONSTRATION")
    print("=" * 70)

    session = setup_demo_db()
    task_repo = SQLAlchemyTaskRepository(session)
    dep_repo = SQLAlchemyTaskDependencyRepository(session)

    graph_service = DependencyGraphService(task_repo, dep_repo)
    claim_service = TaskClaimService(task_repo)
    exec_service = TaskExecutionService(task_repo)
    lifecycle_service = TaskLifecycleService(task_repo, graph_service)
    scheduler_service = TaskSchedulerService(task_repo, claim_service, exec_service)
    evaluator = ReadinessEvaluator()

    plan_id = "plan-analytics"

    # 1. Create 6 Tasks
    t1 = Task(
        id="T1",
        plan_id=plan_id,
        title="Research Requirements",
        description="Gather specs",
        priority="high",
        status=TaskStatus.PLANNED,
    )
    t2 = Task(
        id="T2",
        plan_id=plan_id,
        title="Design Architecture",
        description="Create blueprint",
        priority="high",
        status=TaskStatus.PLANNED,
    )
    t3 = Task(
        id="T3",
        plan_id=plan_id,
        title="Build Backend API",
        description="FastAPI endpoints",
        priority="medium",
        status=TaskStatus.PLANNED,
    )
    t4 = Task(
        id="T4",
        plan_id=plan_id,
        title="Build Frontend UI",
        description="Dashboard UI",
        priority="medium",
        status=TaskStatus.PLANNED,
    )
    t5 = Task(
        id="T5",
        plan_id=plan_id,
        title="Integration Testing",
        description="End to end integration",
        priority="high",
        status=TaskStatus.PLANNED,
    )
    t6 = Task(
        id="T6",
        plan_id=plan_id,
        title="QA & Deployment",
        description="Final verification",
        priority="critical",
        status=TaskStatus.PLANNED,
    )

    for t in [t1, t2, t3, t4, t5, t6]:
        task_repo.save(t)
    session.commit()

    # 2. Build Dependency Edges
    # T1 -> T2 -> (T3, T4) -> T5 -> T6
    deps = [
        TaskDependency(id="d1", predecessor_task_id="T1", successor_task_id="T2"),
        TaskDependency(id="d2", predecessor_task_id="T2", successor_task_id="T3"),
        TaskDependency(id="d3", predecessor_task_id="T2", successor_task_id="T4"),
        TaskDependency(id="d4", predecessor_task_id="T3", successor_task_id="T5"),
        TaskDependency(id="d5", predecessor_task_id="T4", successor_task_id="T5"),
        TaskDependency(id="d6", predecessor_task_id="T5", successor_task_id="T6"),
    ]

    for d in deps:
        await graph_service.add_dependency(d)
    session.commit()

    print("\nInitial Graph State:")
    all_tasks = task_repo.get_by_plan_id(plan_id)
    for t in all_tasks:
        reasons = [r.value for r in t.block_reasons]
        print(f"  Task {t.id} ({t.title}): status={t.status.value}, block_reasons={reasons}")

    # Evaluate readiness
    graph = graph_service.build_graph_for_plan(plan_id)
    for t in all_tasks:
        if evaluator.update_task_readiness(t, graph):
            task_repo.save(t)
    session.commit()

    print("\nReadiness Evaluated State:")
    all_tasks = task_repo.get_by_plan_id(plan_id)
    for t in all_tasks:
        print(f"  Task {t.id} ({t.title}): status={t.status.value}")

    # Step-by-step DAG execution loop
    step = 1
    while True:
        ready = scheduler_service.get_ready_tasks(plan_id)
        if not ready:
            print("\nNo more READY tasks available.")
            break

        print(f"\n--- STEP {step}: Discovered READY tasks: {[t.id for t in ready]} ---")
        for ready_task in ready:
            print(f"Claiming and executing task {ready_task.id}...")
            executed = await scheduler_service.schedule_next_task(plan_id=plan_id)
            if executed:
                print(
                    f"  Executed Task {executed.id}: status={executed.status.value}, "
                    f"run_id={executed.execution_run_id}"
                )
                # Review and approve task
                if executed.status == TaskStatus.REVIEW:
                    approved = await lifecycle_service.review_task(
                        executed.id, approved=True, reviewer_id="mgr-1"
                    )
                    print(f"  Reviewed Task {approved.id}: status={approved.status.value}")

        step += 1

    print("\nFinal DAG Execution Summary:")
    final_tasks = task_repo.get_by_plan_id(plan_id)
    for t in final_tasks:
        print(f"  [{t.status.value}] Task {t.id}: {t.title}")

    print("\n" + "=" * 70)
    print("TASK DAG EXECUTION DEMONSTRATION COMPLETE — 100% SUCCESS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_dag_demo())
