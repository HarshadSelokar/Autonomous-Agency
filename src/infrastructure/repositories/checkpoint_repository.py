"""
SQLAlchemy implementation of CheckpointRepositoryInterface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.checkpoint import AgentCheckpoint
from src.domain.repository import CheckpointRepositoryInterface
from src.infrastructure.models.checkpoint_model import (
    AgentCheckpointModel,
    checkpoint_domain_to_model,
    checkpoint_model_to_domain,
)


class SQLAlchemyCheckpointRepository(CheckpointRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, checkpoint: AgentCheckpoint) -> AgentCheckpoint:
        """Save an AgentCheckpoint entity."""
        model = await self.session.get(AgentCheckpointModel, checkpoint.id)
        if model is None:
            model = checkpoint_domain_to_model(checkpoint)
            self.session.add(model)
        else:
            updated_model = checkpoint_domain_to_model(checkpoint)
            model.current_state = updated_model.current_state
            model.current_step = updated_model.current_step
            model.context_reference_json = updated_model.context_reference_json
            model.output_so_far_json = updated_model.output_so_far_json
            model.metadata_json = updated_model.metadata_json

        await self.session.flush()
        return checkpoint_model_to_domain(model)

    async def get_latest_by_run_id(self, run_id: str) -> AgentCheckpoint | None:
        """Find the latest checkpoint for a specific run."""
        stmt = (
            select(AgentCheckpointModel)
            .where(AgentCheckpointModel.run_id == run_id)
            .order_by(AgentCheckpointModel.current_step.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return checkpoint_model_to_domain(model)

    async def list_by_run_id(self, run_id: str) -> list[AgentCheckpoint]:
        """List all checkpoints for a specific run ordered by timestamp."""
        stmt = (
            select(AgentCheckpointModel)
            .where(AgentCheckpointModel.run_id == run_id)
            .order_by(AgentCheckpointModel.current_step.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [checkpoint_model_to_domain(m) for m in models]
