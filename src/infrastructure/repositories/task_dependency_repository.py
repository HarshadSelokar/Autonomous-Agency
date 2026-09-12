"""
SQLAlchemy Repository implementation for TaskDependency domain entity.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.task_dependency import TaskDependency
from src.infrastructure.models.task_dependency_model import (
    TaskDependencyModel,
    task_dependency_domain_to_model,
    task_dependency_model_to_domain,
)


class SQLAlchemyTaskDependencyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, dependency: TaskDependency) -> TaskDependency:
        model = self.session.get(TaskDependencyModel, dependency.id)
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
        self.session.flush()
        return task_dependency_model_to_domain(model)

    def get_by_id(self, dependency_id: str) -> TaskDependency | None:
        model = self.session.get(TaskDependencyModel, dependency_id)
        if model is None:
            return None
        return task_dependency_model_to_domain(model)

    def get_by_plan_id(self, plan_id: str) -> list[TaskDependency]:
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
        models: Sequence[TaskDependencyModel] = self.session.scalars(stmt).all()
        return [task_dependency_model_to_domain(m) for m in models]

    def get_all(self) -> list[TaskDependency]:
        stmt = select(TaskDependencyModel)
        models: Sequence[TaskDependencyModel] = self.session.scalars(stmt).all()
        return [task_dependency_model_to_domain(m) for m in models]

    def delete(self, dependency_id: str) -> None:
        model = self.session.get(TaskDependencyModel, dependency_id)
        if model is not None:
            self.session.delete(model)
            self.session.flush()
