"""
SQLAlchemy Repository implementation for Workspace domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.workspace import Workspace
from src.infrastructure.models.workspace_model import (
    WorkspaceModel,
    workspace_domain_to_model,
    workspace_model_to_domain,
)


class SQLAlchemyWorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, workspace: Workspace) -> Workspace:
        model = workspace_domain_to_model(workspace)
        merged = await self.session.merge(model)
        await self.session.flush()
        return workspace_model_to_domain(merged)

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        stmt = select(WorkspaceModel).where(WorkspaceModel.id == workspace_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return workspace_model_to_domain(model) if model else None

    async def get_by_task_id(self, task_id: str) -> Workspace | None:
        stmt = select(WorkspaceModel).where(WorkspaceModel.task_id == task_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return workspace_model_to_domain(model) if model else None

    async def list_all(self) -> list[Workspace]:
        stmt = select(WorkspaceModel).order_by(WorkspaceModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [workspace_model_to_domain(m) for m in models]
