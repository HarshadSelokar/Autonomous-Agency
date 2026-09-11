"""
Integration tests for Agent repository persistence using async SQLAlchemy.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.agent import Agent, AgentState, ModelConfiguration, PermissionProfile
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository


@pytest.fixture
async def async_session() -> AsyncSession:
    # Use SQLite in-memory for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_agent_repository_save_and_get(async_session: AsyncSession) -> None:
    repo = SQLAlchemyAgentRepository(async_session)

    agent = Agent(
        id="agent_001",
        name="Research Assistant",
        role="Researcher",
        responsibilities=["Conduct research"],
        capabilities=["web_search"],
        model_configuration=ModelConfiguration(provider="groq", model="llama-3.3-70b-versatile"),
        permission_profile=PermissionProfile(permissions=["read_all"]),
    )

    # Save
    saved_agent = await repo.save(agent)
    assert saved_agent.id == "agent_001"

    # Get by ID
    fetched = await repo.get_by_id("agent_001")
    assert fetched is not None
    assert fetched.id == "agent_001"
    assert fetched.name == "Research Assistant"
    assert fetched.current_state == AgentState.IDLE
    assert fetched.permission_profile.has_permission("read_all")


@pytest.mark.asyncio
async def test_agent_repository_update_and_state_change(async_session: AsyncSession) -> None:
    repo = SQLAlchemyAgentRepository(async_session)

    agent = Agent(id="agent_002", name="Coder", role="Developer")
    await repo.save(agent)

    # Transition state
    agent.transition_to(AgentState.READY)
    agent.transition_to(AgentState.RUNNING)
    await repo.save(agent)

    updated = await repo.get_by_id("agent_002")
    assert updated is not None
    assert updated.current_state == AgentState.RUNNING


@pytest.mark.asyncio
async def test_agent_repository_list_and_delete(async_session: AsyncSession) -> None:
    repo = SQLAlchemyAgentRepository(async_session)

    a1 = Agent(id="agent_101", name="Agent One", role="Role 1")
    a2 = Agent(id="agent_102", name="Agent Two", role="Role 2")

    await repo.save(a1)
    await repo.save(a2)

    all_agents = await repo.list_all()
    assert len(all_agents) == 2

    # Delete
    deleted = await repo.delete("agent_101")
    assert deleted is True

    remaining = await repo.list_all()
    assert len(remaining) == 1
    assert remaining[0].id == "agent_102"
