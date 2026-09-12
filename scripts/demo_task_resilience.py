"""
Phase 4 Resilience Demonstration Script.
Demonstrates:
1. Self-dependency rejection (T1 -> T1)
2. Direct cycle rejection (T1 -> T2 -> T1)
3. Multi-level cycle rejection (T1 -> T2 -> T3 -> T1)
4. Atomic claiming race condition protection
5. Predecessor failure blocking downstream execution
6. Review -> Rework -> Review -> Approved lifecycle flow
"""

import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.application.dependency_graph_service import DependencyGraphService
from src.application.task_claim_service import TaskClaimService
from src.application.task_execution_service import TaskExecutionService
from src.application.task_lifecycle_service import TaskLifecycleService
from src.domain.exceptions import TaskClaimError, TaskCycleError, TaskDependencyError
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


def setup_resilience_db():
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
        id="obj-resilience",
        title="Resilience Testing",
        description="Resilience test scenario",
        requester="QA",
        status="APPROVED",
        constraints_json=[],
        metadata_json={},
    )
    plan = PlanModel(
        id="plan-resilience",
        objective_id="obj-resilience",
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


async def run_resilience_demo() -> None:
    print("=" * 70)
    print("PHASE 4 — TASK ENGINE RESILIENCE DEMONSTRATION")
    print("=" * 70)

    session = setup_resilience_db()
    task_repo = SQLAlchemyTaskRepository(session)
    dep_repo = SQLAlchemyTaskDependencyRepository(session)

    graph_service = DependencyGraphService(task_repo, dep_repo)
    claim_service = TaskClaimService(task_repo)
    exec_service = TaskExecutionService(task_repo)
    lifecycle_service = TaskLifecycleService(task_repo, graph_service)

    plan_id = "plan-resilience"

    # Demo 1: Self-dependency rejection
    print("\n1. DEMO: Self-dependency Rejection (T1 -> T1)")
    t1 = Task(
        id="T1", plan_id=plan_id, title="Task 1", description="Desc 1", status=TaskStatus.PLANNED
    )
    task_repo.save(t1)
    session.commit()

    try:
        await graph_service.add_dependency(
            TaskDependency(id="d-self", predecessor_task_id="T1", successor_task_id="T1")
        )
    except TaskDependencyError as err:
        print(f"  [SUCCESSFULLY REJECTED] {err}")

    # Demo 2: Direct Cycle Rejection (T1 -> T2 -> T1)
    print("\n2. DEMO: Direct Cycle Rejection (T1 -> T2 -> T1)")
    t2 = Task(
        id="T2", plan_id=plan_id, title="Task 2", description="Desc 2", status=TaskStatus.PLANNED
    )
    task_repo.save(t2)
    session.commit()

    await graph_service.add_dependency(
        TaskDependency(id="d12", predecessor_task_id="T1", successor_task_id="T2")
    )
    session.commit()

    try:
        await graph_service.add_dependency(
            TaskDependency(id="d21", predecessor_task_id="T2", successor_task_id="T1")
        )
    except TaskCycleError as err:
        print(f"  [SUCCESSFULLY REJECTED] {err}")

    # Demo 3: Multi-level Cycle Rejection (T1 -> T2 -> T3 -> T1)
    print("\n3. DEMO: Multi-level Cycle Rejection (T1 -> T2 -> T3 -> T1)")
    t3 = Task(
        id="T3", plan_id=plan_id, title="Task 3", description="Desc 3", status=TaskStatus.PLANNED
    )
    task_repo.save(t3)
    session.commit()

    await graph_service.add_dependency(
        TaskDependency(id="d23", predecessor_task_id="T2", successor_task_id="T3")
    )
    session.commit()

    try:
        await graph_service.add_dependency(
            TaskDependency(id="d31", predecessor_task_id="T3", successor_task_id="T1")
        )
    except TaskCycleError as err:
        print(f"  [SUCCESSFULLY REJECTED] {err}")

    # Demo 4: Atomic Claim Race Condition
    print("\n4. DEMO: Atomic Claim Race Condition Protection")
    t1.status = TaskStatus.READY
    task_repo.save(t1)
    session.commit()

    worker1_claim = claim_service.claim_task("T1", worker_id="worker-1")
    print(f"  Worker 1 claimed task T1: status={worker1_claim.status.value}")

    try:
        claim_service.claim_task("T1", worker_id="worker-2")
    except TaskClaimError as err:
        print(f"  Worker 2 claim rejected: {err}")

    # Demo 5: Predecessor Failure Blocking Downstream Task
    print("\n5. DEMO: Predecessor Failure Blocking Downstream Execution")
    t1.status = TaskStatus.FAILED
    task_repo.save(t1)
    graph_service.propagate_task_state_change("T1")
    session.commit()

    t2_updated = task_repo.get_by_id("T2")
    reasons_list = [r.value for r in t2_updated.block_reasons]
    print(f"  Task T2 status: status={t2_updated.status.value}, reasons={reasons_list}")
    assert t2_updated.status == TaskStatus.BLOCKED

    # Demo 6: Review -> Rework -> Review -> Approved Lifecycle Flow
    print("\n6. DEMO: Review -> Rework -> Review -> Approved Lifecycle Flow")
    t_demo = Task(
        id="T-DEMO",
        plan_id=plan_id,
        title="Rework Test",
        description="Rework flow",
        status=TaskStatus.READY,
    )
    task_repo.save(t_demo)
    session.commit()

    executed = await exec_service.execute_task(
        t_demo, employee_id="emp-1", assignment_id="asgn-demo"
    )
    print(f"  Initial Execution Task status: {executed.status.value}")

    # Reject during review
    reworked = await lifecycle_service.review_task(
        "T-DEMO", approved=False, reviewer_id="mgr-1", feedback="Add exception handling"
    )
    fb = reworked.metadata["rework_history"][0]["feedback"]
    print(f"  Reviewed (Rejected) status: {reworked.status.value}, feedback='{fb}'")

    # Re-execute after rework
    re_executed = await exec_service.execute_task(
        reworked, employee_id="emp-1", assignment_id="asgn-demo"
    )
    print(f"  Re-executed status: {re_executed.status.value}")

    # Approve on second review
    approved = await lifecycle_service.review_task("T-DEMO", approved=True, reviewer_id="mgr-1")
    print(f"  Final Review (Approved) status: {approved.status.value}")

    print("\n" + "=" * 70)
    print("TASK ENGINE RESILIENCE DEMONSTRATION COMPLETE — ALL GAARDS ACTIVE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_resilience_demo())
