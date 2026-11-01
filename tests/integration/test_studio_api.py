"""Integration tests for the Software Studio API, end to end with a scripted model."""

import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.api.routes.studio import get_studio
from src.application.agent_loop import AgentLoop
from src.application.dev_team_service import DevTeamOrchestrator
from src.application.provider_registry import ModelProviderRegistry
from src.application.retry import RetryPolicy
from src.application.studio_service import StudioService
from src.domain.dev_project import ActivityEvent
from src.infrastructure.coding.command_runner import CommandRunner
from src.infrastructure.database import Base
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.repositories.dev_project_repository import SQLAlchemyDevProjectStore

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")

PLAN = json.dumps(
    {
        "summary": "Add a greeting module.",
        "test_command": None,
        "tickets": [{"title": "Add greet()", "description": "d", "acceptance_criteria": "c", "depends_on": []}],
    }
)


@pytest.fixture
async def studio_env(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'studio.db'}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    provider = FakeModelProvider()
    registry = ModelProviderRegistry()
    registry.register(provider)
    broadcast: list[ActivityEvent] = []

    async def on_activity(event: ActivityEvent) -> None:
        broadcast.append(event)

    def orchestrator_factory(store: Any, listener: Any) -> DevTeamOrchestrator:
        return DevTeamOrchestrator(
            store=store,
            agent_loop=AgentLoop(provider_registry=registry, retry_policy=RetryPolicy(max_retries=0), max_steps=6),
            runner=CommandRunner(allowed_commands=["python", "git"]),
            on_activity=listener,
            max_rework_rounds=0,
            workspaces_dir=str(tmp_path / "workspaces"),
        )

    studio = StudioService(
        store=SQLAlchemyDevProjectStore(async_sessionmaker(engine, expire_on_commit=False)),
        on_activity=on_activity,
        orchestrator_factory=orchestrator_factory,
    )
    app.dependency_overrides[get_studio] = lambda: studio
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, studio, provider, broadcast
    app.dependency_overrides.clear()
    await studio.shutdown()
    await engine.dispose()


async def test_project_runs_to_completion_through_the_api(studio_env):
    client, studio, provider, broadcast = studio_env
    provider.script(content=PLAN)
    provider.script(
        tool_calls=[{"id": "c1", "name": "write_file", "arguments": {"path": "greet.py", "content": "def greet():\n    return 'hi'\n"}}]
    )
    provider.script(content="Added greet().")
    provider.script(content='{"approved": true, "feedback": "Looks right."}')

    created = await client.post(
        "/studio/projects",
        json={"name": "Greeter", "goal": "Create a module with a greet function.", "provider": "fake", "model": "fake"},
    )
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    assert created.json()["status"] == "PLANNING"
    assert created.json()["is_running"] is True

    # A second start while it is running is refused
    assert (await client.post(f"/studio/projects/{project_id}/start")).status_code == 409

    await studio.wait(project_id)

    detail = (await client.get(f"/studio/projects/{project_id}")).json()
    assert detail["status"] == "COMPLETED", detail["failure_reason"]
    assert detail["is_running"] is False
    assert detail["branch"] == f"agency/{project_id}"
    assert [t["status"] for t in detail["tickets"]] == ["DONE"]
    assert {m["role"] for m in detail["team"]} == {"MANAGER", "DEVELOPER", "QA", "REVIEWER"}
    assert all(m["state"] == "IDLE" for m in detail["team"])  # nobody is working once it is done

    board = (await client.get(f"/studio/projects/{project_id}/board")).json()
    assert [t["title"] for t in board["DONE"]] == ["Add greet()"]
    assert board["TODO"] == []

    events = (await client.get(f"/studio/projects/{project_id}/events")).json()
    assert ("DEVELOPER", "writing greet.py") in [(e["actor_role"], e["summary"]) for e in events]
    assert len(broadcast) == len(events)  # every persisted event was also pushed live

    last_seen = events[2]["sequence"]
    later = (await client.get(f"/studio/projects/{project_id}/events", params={"after": last_seen})).json()
    assert [e["sequence"] for e in later] == [e["sequence"] for e in events[3:]]

    diff = (await client.get(f"/studio/projects/{project_id}/diff")).json()
    assert [c["subject"] for c in diff["commits"]] == ["Add greet()"]
    assert "+def greet():" in diff["diff"]

    listed = (await client.get("/studio/projects")).json()
    assert [p["id"] for p in listed] == [project_id]


async def test_create_without_auto_start_then_cancel_is_a_noop(studio_env):
    client, studio, provider, _ = studio_env
    created = await client.post(
        "/studio/projects",
        json={"name": "Idle", "goal": "Do nothing yet, just exist.", "auto_start": False},
    )
    project_id = created.json()["id"]
    assert created.json()["status"] == "CREATED"
    assert created.json()["is_running"] is False

    cancel = (await client.post(f"/studio/projects/{project_id}/cancel")).json()
    assert cancel["cancel_requested"] is False
    assert provider.call_count == 0


async def test_request_validation(studio_env):
    client, _, _, _ = studio_env
    base = {"name": "P", "goal": "A sufficiently long goal."}

    assert (await client.post("/studio/projects", json={**base, "repo_url": "git@host:x.git"})).status_code == 422
    assert (
        await client.post("/studio/projects", json={**base, "repo_url": "https://h/x.git", "local_path": "/tmp"})
    ).status_code == 422
    assert (await client.post("/studio/projects", json={**base, "local_path": "/definitely/not/a/repo"})).status_code == 422
    assert (await client.post("/studio/projects", json={"name": "P", "goal": "short"})).status_code == 422
    assert (await client.get("/studio/projects/prj-missing")).status_code == 404


async def test_interrupted_projects_are_marked_on_startup(studio_env):
    client, studio, _, _ = studio_env
    created = await client.post(
        "/studio/projects", json={"name": "Stale", "goal": "Was running when the process died.", "auto_start": False}
    )
    project_id = created.json()["id"]
    project = await studio.store.get_project(project_id)
    from src.domain.dev_project import ProjectStatus

    project.set_status(ProjectStatus.RUNNING)
    await studio.store.save_project(project)

    assert await studio.recover_interrupted(resume=False) == [project_id]
    assert (await client.get(f"/studio/projects/{project_id}")).json()["status"] == "INTERRUPTED"
