"""
SQLAlchemy Repository implementation for Artifact domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.artifact import Artifact
from src.infrastructure.models.artifact_model import (
    ArtifactModel,
    artifact_domain_to_model,
    artifact_model_to_domain,
)


class SQLAlchemyArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, artifact: Artifact) -> Artifact:
        model = artifact_domain_to_model(artifact)
        merged = await self.session.merge(model)
        await self.session.flush()
        return artifact_model_to_domain(merged)

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return artifact_model_to_domain(model) if model else None

    async def list_by_workspace_id(self, workspace_id: str) -> list[Artifact]:
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.workspace_id == workspace_id)
            .order_by(ArtifactModel.version.desc())
        )
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [artifact_model_to_domain(m) for m in models]

    async def list_all(self) -> list[Artifact]:
        stmt = select(ArtifactModel).order_by(ArtifactModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [artifact_model_to_domain(m) for m in models]
