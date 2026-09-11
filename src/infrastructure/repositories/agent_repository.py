"""
SQLAlchemy implementation of AgentRepositoryInterface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.agent import Agent
from src.domain.repository import AgentRepositoryInterface
from src.infrastructure.models.agent_model import (
    AgentModel,
    agent_domain_to_model,
    agent_model_to_domain,
)


class SQLAlchemyAgentRepository(AgentRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, agent: Agent) -> Agent:
        """Save or update an Agent entity."""
        model = await self.session.get(AgentModel, agent.id)
        if model is None:
            model = agent_domain_to_model(agent)
            self.session.add(model)
        else:
            # Update fields on existing model
            updated_model = agent_domain_to_model(agent)
            model.name = updated_model.name
            model.role = updated_model.role
            model.description = updated_model.description
            model.responsibilities = updated_model.responsibilities
            model.capabilities = updated_model.capabilities
            model.manager_id = updated_model.manager_id
            model.model_configuration = updated_model.model_configuration
            model.permission_profile = updated_model.permission_profile
            model.verification_policy = updated_model.verification_policy
            model.communication_policy = updated_model.communication_policy
            model.current_state = updated_model.current_state
            model.current_task_id = updated_model.current_task_id
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at

        await self.session.flush()
        return agent_model_to_domain(model)

    async def get_by_id(self, agent_id: str) -> Agent | None:
        """Find an Agent entity by its ID."""
        model = await self.session.get(AgentModel, agent_id)
        if model is None:
            return None
        return agent_model_to_domain(model)

    async def list_all(self) -> list[Agent]:
        """List all persisted Agent entities."""
        stmt = select(AgentModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [agent_model_to_domain(m) for m in models]

    async def delete(self, agent_id: str) -> bool:
        """Delete an Agent entity by ID. Returns True if deleted."""
        model = await self.session.get(AgentModel, agent_id)
        if model is None:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
