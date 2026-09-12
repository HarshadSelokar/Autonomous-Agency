"""
Integration tests for TaskRepository and TaskDependencyRepository using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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


def setup_in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Create dummy Objective and Plan for FK constraints
    obj = ObjectiveModel(
        id="obj-1",
        title="Test Objective",
        description="Test Desc",
        requester="User",
        status="APPROVED",
        constraints_json=[],
        metadata_json={},
    )
    plan = PlanModel(
        id="plan-1",
        objective_id="obj-1",
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


def test_task_repository_crud() -> None:
    session = setup_in_memory_db()
    repo = SQLAlchemyTaskRepository(session)

    t1 = Task(
        id="task-100",
        plan_id="plan-1",
        title="Repo Test Task",
        description="Testing persistence",
        priority="high",
    )

    saved_t1 = repo.save(t1)
    session.commit()

    assert saved_t1.id == "task-100"
    fetched = repo.get_by_id("task-100")
    assert fetched.title == "Repo Test Task"
    assert fetched.priority == "high"
    assert fetched.status == TaskStatus.CREATED

    # Update status
    fetched.status = TaskStatus.PLANNED
    repo.save(fetched)
    session.commit()

    updated = repo.get_by_id("task-100")
    assert updated.status == TaskStatus.PLANNED

    by_plan = repo.get_by_plan_id("plan-1")
    assert len(by_plan) == 1


def test_task_dependency_repository_crud() -> None:
    session = setup_in_memory_db()
    task_repo = SQLAlchemyTaskRepository(session)
    dep_repo = SQLAlchemyTaskDependencyRepository(session)

    t1 = Task(id="t1", plan_id="plan-1", title="T1", description="D1")
    t2 = Task(id="t2", plan_id="plan-1", title="T2", description="D2")
    task_repo.save(t1)
    task_repo.save(t2)
    session.commit()

    dep = TaskDependency(id="dep-1", predecessor_task_id="t1", successor_task_id="t2")
    saved_dep = dep_repo.save(dep)
    session.commit()

    assert saved_dep.id == "dep-1"
    fetched_dep = dep_repo.get_by_id("dep-1")
    assert fetched_dep is not None
    assert fetched_dep.predecessor_task_id == "t1"
    assert fetched_dep.successor_task_id == "t2"
