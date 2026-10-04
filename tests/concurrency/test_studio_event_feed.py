"""Concurrency test: parallel developers writing one project's activity feed."""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.dev_project import ActivityEvent, DevProject
from src.infrastructure.database import Base
from src.infrastructure.repositories.dev_project_repository import SQLAlchemyDevProjectStore


async def test_concurrent_events_get_unique_consecutive_sequences(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'feed.db'}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    store = SQLAlchemyDevProjectStore(async_sessionmaker(engine, expire_on_commit=False))
    await store.save_project(DevProject(id="prj-1", name="P", goal="g"))

    def event(index: int) -> ActivityEvent:
        return ActivityEvent(
            project_id="prj-1", actor_id=f"dev-{index % 3}", actor_name="D", actor_role="DEVELOPER",
            kind="tool_call", summary=f"step {index}",
        )

    written = await asyncio.gather(*(store.add_event(event(i)) for i in range(60)))

    assert sorted(e.sequence for e in written) == list(range(1, 61))
    stored = await store.list_events("prj-1", limit=1000)
    assert [e.sequence for e in stored] == list(range(1, 61))
    assert {e.summary for e in stored} == {f"step {i}" for i in range(60)}
    await engine.dispose()
