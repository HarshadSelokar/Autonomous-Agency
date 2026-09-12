"""
SQLAlchemy Repository implementation for Task domain entity.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.exceptions import TaskNotFoundError
from src.domain.task import Task, TaskStatus
from src.infrastructure.models.task_model import (
    TaskModel,
    task_domain_to_model,
    task_model_to_domain,
)


class SQLAlchemyTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, task: Task) -> Task:
        model = self.session.get(TaskModel, task.id)
        if model is None:
            model = task_domain_to_model(task)
            self.session.add(model)
        else:
            updated_model = task_domain_to_model(task)
            model.plan_id = updated_model.plan_id
            model.objective_id = updated_model.objective_id
            model.work_item_id = updated_model.work_item_id
            model.parent_task_id = updated_model.parent_task_id
            model.title = updated_model.title
            model.description = updated_model.description
            model.required_capabilities_json = updated_model.required_capabilities_json
            model.priority = updated_model.priority
            model.status = updated_model.status
            model.assigned_employee_id = updated_model.assigned_employee_id
            model.assignment_id = updated_model.assignment_id
            model.execution_run_id = updated_model.execution_run_id
            model.retry_count = updated_model.retry_count
            model.max_retries = updated_model.max_retries
            model.block_reasons_json = updated_model.block_reasons_json
            model.result_json = updated_model.result_json
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at
        self.session.flush()
        return task_model_to_domain(model)

    def get_by_id(self, task_id: str) -> Task:
        model = self.session.get(TaskModel, task_id)
        if model is None:
            raise TaskNotFoundError(task_id)
        return task_model_to_domain(model)

    def get_by_plan_id(self, plan_id: str) -> list[Task]:
        stmt = select(TaskModel).where(TaskModel.plan_id == plan_id)
        models: Sequence[TaskModel] = self.session.scalars(stmt).all()
        return [task_model_to_domain(m) for m in models]

    def get_by_status(self, status: TaskStatus) -> list[Task]:
        stmt = select(TaskModel).where(TaskModel.status == status.value)
        models: Sequence[TaskModel] = self.session.scalars(stmt).all()
        return [task_model_to_domain(m) for m in models]

    def get_all(self) -> list[Task]:
        stmt = select(TaskModel)
        models: Sequence[TaskModel] = self.session.scalars(stmt).all()
        return [task_model_to_domain(m) for m in models]

    def delete(self, task_id: str) -> None:
        model = self.session.get(TaskModel, task_id)
        if model is not None:
            self.session.delete(model)
            self.session.flush()
