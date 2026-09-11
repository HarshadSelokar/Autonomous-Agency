"""
SQLAlchemy implementation of AgentRunRepositoryInterface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repository import AgentRunRepositoryInterface
from src.domain.run import AgentRun
from src.infrastructure.models.run_model import (
    AgentRunModel,
    run_domain_to_model,
    run_model_to_domain,
)


class SQLAlchemyAgentRunRepository(AgentRunRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, run: AgentRun) -> AgentRun:
        """Save or update an AgentRun entity."""
        model = await self.session.get(AgentRunModel, run.id)
        if model is None:
            model = run_domain_to_model(run)
            self.session.add(model)
        else:
            updated_model = run_domain_to_model(run)
            model.status = updated_model.status
            model.provider = updated_model.provider
            model.model = updated_model.model
            model.started_at = updated_model.started_at
            model.completed_at = updated_model.completed_at
            model.failure_reason = updated_model.failure_reason
            model.usage_json = updated_model.usage_json
            model.result_json = updated_model.result_json
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at

        await self.session.flush()
        return run_model_to_domain(model)

    async def get_by_id(self, run_id: str) -> AgentRun | None:
        """Find an AgentRun entity by ID."""
        model = await self.session.get(AgentRunModel, run_id)
        if model is None:
            return None
        return run_model_to_domain(model)

    async def list_by_agent_id(self, agent_id: str) -> list[AgentRun]:
        """List all AgentRuns for a specific agent."""
        stmt = select(AgentRunModel).where(AgentRunModel.agent_id == agent_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [run_model_to_domain(m) for m in models]
