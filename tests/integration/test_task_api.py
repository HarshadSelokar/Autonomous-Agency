"""
Integration tests for Task & Scheduler REST API endpoints using FastAPI TestClient.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.infrastructure.database import Base, get_db
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


test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
Base.metadata.create_all(test_engine)
TestSessionFactory = sessionmaker(bind=test_engine)
test_session = TestSessionFactory()

# Pre-populate dummy Objective and Plan
obj = ObjectiveModel(
    id="obj-1",
    title="API Test Obj",
    description="Desc",
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
test_session.add(obj)
test_session.add(plan)
test_session.commit()


def override_get_db():
    try:
        yield test_session
    finally:
        pass


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_get_list_tasks_api() -> None:
    # 1. Create task
    response = client.post(
        "/tasks",
        json={
            "plan_id": "plan-1",
            "title": "Build Backend API",
            "description": "Create FastAPI endpoints for task engine",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    task_data = response.json()
    task_id = task_data["id"]
    assert task_data["title"] == "Build Backend API"
    assert task_data["status"] == "READY"

    # 2. Get task
    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id

    # 3. List ready tasks
    ready_res = client.get("/tasks/ready")
    assert ready_res.status_code == 200
    assert len(ready_res.json()) >= 1


def test_add_dependency_and_cycle_rejection_api() -> None:
    # Create T1 and T2
    t1_res = client.post(
        "/tasks",
        json={"plan_id": "plan-1", "title": "T1", "description": "D1"},
    )
    t2_res = client.post(
        "/tasks",
        json={"plan_id": "plan-1", "title": "T2", "description": "D2"},
    )
    t1_id = t1_res.json()["id"]
    t2_id = t2_res.json()["id"]

    # Add T1 -> T2 dependency
    dep_res = client.post(
        f"/tasks/{t2_id}/dependencies",
        json={
            "predecessor_task_id": t1_id,
            "successor_task_id": t2_id,
        },
    )
    assert dep_res.status_code == 201

    # Attempting T2 -> T1 dependency should fail with 400 Bad Request due to cycle
    cycle_res = client.post(
        f"/tasks/{t1_id}/dependencies",
        json={
            "predecessor_task_id": t2_id,
            "successor_task_id": t1_id,
        },
    )
    assert cycle_res.status_code == 400
    assert "creates a dependency cycle" in cycle_res.json()["detail"]


def test_scheduler_run_api() -> None:
    res = client.post(
        "/scheduler/run",
        json={"worker_id": "api-worker", "plan_id": "plan-1", "max_tasks": 5},
    )
    assert res.status_code == 200
    data = res.json()
    assert "processed_tasks" in data
