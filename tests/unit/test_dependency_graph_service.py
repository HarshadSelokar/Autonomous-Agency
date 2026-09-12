"""
Unit tests for DependencyGraphService managing graph operations and state propagation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.dependency_graph_service import DependencyGraphService
from src.domain.exceptions import TaskCycleError
from src.domain.task import BlockReason, Task, TaskStatus
from src.domain.task_dependency import TaskDependency


@pytest.mark.asyncio
async def test_dependency_graph_service_add_dependency() -> None:
    task_repo = MagicMock()
    dep_repo = MagicMock()
    event_dispatcher = MagicMock()
    event_dispatcher.publish = AsyncMock()

    service = DependencyGraphService(
        task_repository=task_repo,
        dependency_repository=dep_repo,
        event_dispatcher=event_dispatcher,
    )

    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.IN_PROGRESS)
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2", status=TaskStatus.PLANNED)

    task_repo.get_by_id.side_effect = lambda tid: t1 if tid == "t1" else t2
    task_repo.get_by_plan_id.return_value = [t1, t2]
    dep_repo.get_by_plan_id.return_value = []
    dep_repo.save.side_effect = lambda d: d

    dep = TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="t2")
    saved = await service.add_dependency(dep)

    assert saved.id == "d1"
    dep_repo.save.assert_called_once_with(dep)
    assert t2.status == TaskStatus.BLOCKED
    assert BlockReason.DEPENDENCY_INCOMPLETE in t2.block_reasons
    event_dispatcher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_dependency_graph_service_cycle_rejected() -> None:
    task_repo = MagicMock()
    dep_repo = MagicMock()

    service = DependencyGraphService(
        task_repository=task_repo,
        dependency_repository=dep_repo,
    )

    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1")
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2")

    existing_dep = TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="t2")

    task_repo.get_by_id.side_effect = lambda tid: t1 if tid == "t1" else t2
    task_repo.get_by_plan_id.return_value = [t1, t2]
    dep_repo.get_by_plan_id.return_value = [existing_dep]

    # Attempting to add t2 -> t1 creates cycle t1 -> t2 -> t1
    new_dep = TaskDependency(id="d2", predecessor_task_id="t2", successor_task_id="t1")

    with pytest.raises(TaskCycleError, match="creates a dependency cycle"):
        await service.add_dependency(new_dep)


@pytest.mark.asyncio
async def test_dependency_graph_service_propagation() -> None:
    task_repo = MagicMock()
    dep_repo = MagicMock()

    service = DependencyGraphService(
        task_repository=task_repo,
        dependency_repository=dep_repo,
    )

    t1 = Task(id="t1", plan_id="p1", title="T1", description="D1", status=TaskStatus.COMPLETED)
    t2 = Task(id="t2", plan_id="p1", title="T2", description="D2", status=TaskStatus.BLOCKED)

    existing_dep = TaskDependency(id="d1", predecessor_task_id="t1", successor_task_id="t2")

    task_repo.get_by_id.return_value = t1
    task_repo.get_by_plan_id.return_value = [t1, t2]
    dep_repo.get_by_plan_id.return_value = [existing_dep]

    updated = await service.propagate_task_state_change("t1")
    assert len(updated) == 1
    assert updated[0].id == "t2"
    assert t2.status == TaskStatus.READY
