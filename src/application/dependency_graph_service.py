"""
Dependency Graph Application Service for graph persistence, cycle validation,
and readiness state propagation.
"""

import inspect
from typing import Any

from src.application.event_dispatcher import EventDispatcher
from src.application.readiness_evaluator import ReadinessEvaluator
from src.domain.events import TaskDependencyAddedEvent, TaskDependencyRemovedEvent
from src.domain.task import Task
from src.domain.task_dependency import TaskDependency
from src.domain.task_graph import TaskGraph
from src.infrastructure.repositories.task_dependency_repository import (
    SQLAlchemyTaskDependencyRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


async def _maybe_await(res: Any) -> Any:
    if inspect.isawaitable(res):
        return await res
    return res


class DependencyGraphService:
    """
    Application Service for managing task dependency graphs, ensuring pre-persistence
    cycle rejection, and propagating task readiness state changes across downstream successors.
    """

    def __init__(
        self,
        task_repository: SQLAlchemyTaskRepository,
        dependency_repository: SQLAlchemyTaskDependencyRepository,
        readiness_evaluator: ReadinessEvaluator | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.task_repo = task_repository
        self.dep_repo = dependency_repository
        self.evaluator = readiness_evaluator or ReadinessEvaluator()
        self.event_dispatcher = event_dispatcher

    async def build_graph_for_plan(self, plan_id: str) -> TaskGraph:
        """Load tasks and dependencies from DB for plan_id and assemble TaskGraph."""
        graph = TaskGraph()
        tasks = await _maybe_await(self.task_repo.get_by_plan_id(plan_id))
        for task in tasks:
            graph.add_task(task)

        deps = await _maybe_await(self.dep_repo.get_by_plan_id(plan_id))
        for dep in deps:
            graph.add_dependency(dep)
        return graph

    async def add_dependency(self, dependency: TaskDependency) -> TaskDependency:
        """
        Validate cycle, persist dependency edge, re-evaluate successor task readiness,
        and dispatch TaskDependencyAddedEvent.
        """
        pred_task = await _maybe_await(self.task_repo.get_by_id(dependency.predecessor_task_id))
        graph = await self.build_graph_for_plan(pred_task.plan_id)

        # Graph in-memory validation (raises TaskCycleError / TaskDependencyError if invalid)
        graph.add_dependency(dependency)

        # Persist dependency
        saved_dep = await _maybe_await(self.dep_repo.save(dependency))

        # Re-evaluate successor readiness
        succ_task = graph.get_task(dependency.successor_task_id)
        if self.evaluator.update_task_readiness(succ_task, graph):
            await _maybe_await(self.task_repo.save(succ_task))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    TaskDependencyAddedEvent(
                        dependency_id=saved_dep.id,
                        predecessor_task_id=saved_dep.predecessor_task_id,
                        successor_task_id=saved_dep.successor_task_id,
                        dependency_type=saved_dep.dependency_type.value,
                    )
                )
            )

        return saved_dep

    async def remove_dependency(self, dependency_id: str) -> None:
        """Remove dependency edge and propagate readiness change to affected successor."""
        dep = await _maybe_await(self.dep_repo.get_by_id(dependency_id))
        if dep is None:
            return

        pred_task = await _maybe_await(self.task_repo.get_by_id(dep.predecessor_task_id))
        graph = await self.build_graph_for_plan(pred_task.plan_id)
        graph.remove_dependency(dependency_id)

        await _maybe_await(self.dep_repo.delete(dependency_id))

        succ_task = graph.get_task(dep.successor_task_id)
        if self.evaluator.update_task_readiness(succ_task, graph):
            await _maybe_await(self.task_repo.save(succ_task))

        if self.event_dispatcher:
            await _maybe_await(
                self.event_dispatcher.publish(
                    TaskDependencyRemovedEvent(
                        dependency_id=dep.id,
                        predecessor_task_id=dep.predecessor_task_id,
                        successor_task_id=dep.successor_task_id,
                    )
                )
            )

    async def propagate_task_state_change(self, task_id: str) -> list[Task]:
        """
        Propagate state change of task_id to all downstream successors in the dependency graph.
        Returns list of updated tasks.
        """
        task = await _maybe_await(self.task_repo.get_by_id(task_id))
        graph = await self.build_graph_for_plan(task.plan_id)

        # Update task in graph
        graph.tasks[task.id] = task

        updated_tasks: list[Task] = []
        successors = graph.get_successors(task.id)

        for succ in successors:
            if self.evaluator.update_task_readiness(succ, graph):
                await _maybe_await(self.task_repo.save(succ))
                updated_tasks.append(succ)
                # Recursively propagate to successor's downstream dependencies
                downstream = await self.propagate_task_state_change(succ.id)
                updated_tasks.extend(downstream)

        return updated_tasks
