from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.task import Task, TaskStatus
from src.domain.task_dependency import TaskDependency
from src.infrastructure.database import Base
import src.infrastructure.models  # noqa: F401
from src.infrastructure.models.objective_model import ObjectiveModel
from src.infrastructure.models.plan_model import PlanModel
from src.infrastructure.repositories.task_dependency_repository import (
    SQLAlchemyTaskDependencyRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
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
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_task_repository_crud(async_session: AsyncSession) -> None:
    repo = SQLAlchemyTaskRepository(async_session)

    t1 = Task(
        id="task-100",
        plan_id="plan-1",
        title="Repo Test Task",
        description="Testing persistence",
        priority="high",
    )

    saved_t1 = await repo.save(t1)
    assert saved_t1.id == "task-100"

    fetched = await repo.get_by_id("task-100")
    assert fetched.title == "Repo Test Task"
    assert fetched.priority == "high"
    assert fetched.status == TaskStatus.CREATED

    # Update status
    fetched.status = TaskStatus.PLANNED
    await repo.save(fetched)

    updated = await repo.get_by_id("task-100")
    assert updated.status == TaskStatus.PLANNED

    by_plan = await repo.get_by_plan_id("plan-1")
    assert len(by_plan) == 1


@pytest.mark.asyncio
async def test_task_dependency_repository_crud(async_session: AsyncSession) -> None:
    task_repo = SQLAlchemyTaskRepository(async_session)
    dep_repo = SQLAlchemyTaskDependencyRepository(async_session)

    t1 = Task(id="t1", plan_id="plan-1", title="T1", description="D1")
    t2 = Task(id="t2", plan_id="plan-1", title="T2", description="D2")
    await task_repo.save(t1)
    await task_repo.save(t2)

    dep = TaskDependency(id="dep-1", predecessor_task_id="t1", successor_task_id="t2")
    saved_dep = await dep_repo.save(dep)

    assert saved_dep.id == "dep-1"
    fetched_dep = await dep_repo.get_by_id("dep-1")
    assert fetched_dep is not None
    assert fetched_dep.predecessor_task_id == "t1"
    assert fetched_dep.successor_task_id == "t2"
