"""
SQLAlchemy Repository implementation for TaskDependency domain entity supporting AsyncSession.
"""

import inspect
from typing import Any, Sequence

from sqlalchemy import select

from src.domain.task_dependency import TaskDependency
from src.infrastructure.models.task_dependency_model import (
    TaskDependencyModel,
    task_dependency_domain_to_model,
    task_dependency_model_to_domain,
)


class SQLAlchemyTaskDependencyRepository:
    def __init__(self, session: Any) -> None:
        self.session = session

    async def _get(self, dependency_id: str) -> TaskDependencyModel | None:
        res = self.session.get(TaskDependencyModel, dependency_id)
        if inspect.isawaitable(res):
            return await res
        return res

    async def _scalars_all(self, stmt: Any) -> Sequence[TaskDependencyModel]:
        res = self.session.scalars(stmt)
        if inspect.isawaitable(res):
            res = await res
        all_res = res.all()
        if inspect.isawaitable(all_res):
            all_res = await all_res
        return all_res

    async def save(self, dependency: TaskDependency) -> TaskDependency:
        model = await self._get(dependency.id)
        if model is None:
            model = task_dependency_domain_to_model(dependency)
            self.session.add(model)
        else:
            updated = task_dependency_domain_to_model(dependency)
            model.predecessor_task_id = updated.predecessor_task_id
            model.successor_task_id = updated.successor_task_id
            model.dependency_type = updated.dependency_type
            model.status = updated.status
            model.metadata_json = updated.metadata_json
            model.updated_at = updated.updated_at
        flush_res = self.session.flush()
        if inspect.isawaitable(flush_res):
            await flush_res
        return task_dependency_model_to_domain(model)

    async def get_by_id(self, dependency_id: str) -> TaskDependency | None:
        model = await self._get(dependency_id)
        if model is None:
            return None
        return task_dependency_model_to_domain(model)

    async def get_by_plan_id(self, plan_id: str) -> list[TaskDependency]:
        """Fetch dependencies for all tasks belonging to plan_id."""
        from src.infrastructure.models.task_model import TaskModel

        stmt = (
            select(TaskDependencyModel)
            .join(
                TaskModel,
                TaskDependencyModel.predecessor_task_id == TaskModel.id,
            )
            .where(TaskModel.plan_id == plan_id)
        )
        models = await self._scalars_all(stmt)
        return [task_dependency_model_to_domain(m) for m in models]

    async def get_all(self) -> list[TaskDependency]:
        stmt = select(TaskDependencyModel)
        models = await self._scalars_all(stmt)
        return [task_dependency_model_to_domain(m) for m in models]

    async def delete(self, dependency_id: str) -> None:
        model = await self._get(dependency_id)
        if model is not None:
            delete_res = self.session.delete(model)
            if inspect.isawaitable(delete_res):
                await delete_res
            flush_res = self.session.flush()
            if inspect.isawaitable(flush_res):
                await flush_res
