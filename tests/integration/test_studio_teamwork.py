"""
Integration tests for how the team works together: parallel developers in separate git
worktrees, merge conflicts, human approval, guidance, team changes, quota waits and resume.

A deterministic engine stands in for the model: what each role does is decided by the brief
it receives, so the outcome does not depend on which developer happens to run first.
"""

import asyncio
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.api.routes.studio import get_studio
from src.application.agent_engine import AgentTask
from src.application.agent_loop import AgentLoopResult
from src.application.dev_team_service import DevTeamOrchestrator, InMemoryDevProjectStore
from src.application.studio_service import StudioService
from src.domain.dev_project import DevProject, ProjectStatus, TeamRole, TicketStatus, default_team
from src.domain.exceptions import QuotaExhaustedError
from src.infrastructure.coding.command_runner import CommandRunner
from src.infrastructure.coding.workspace import ProjectWorkspace
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import EmployeeModel
from src.infrastructure.repositories.dev_project_repository import SQLAlchemyDevProjectStore
from src.infrastructure.repositories.studio_team_directory import StudioTeamDirectory

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")

Develop = Callable[[AgentTask, int], Any]


class TeamEngine:
    """Plans the given tickets, lets `develop` do each ticket's work, and reviews as told."""

    def __init__(self, tickets: list[dict[str, Any]], develop: Develop, review: Callable[[AgentTask], dict] | None = None):
        self.tickets = tickets
        self.develop = develop
        self.review = review or (lambda task: {"approved": True, "feedback": "ok"})
        self.developer_briefs: list[str] = []
        self.review_briefs: list[str] = []
        self.attempts: dict[str, int] = {}
        self.active = 0
        self.max_active = 0

    async def run(self, task: AgentTask, *, provider, model, on_event=None, should_cancel=None) -> AgentLoopResult:
        final = task.final_tool["name"] if task.final_tool else None
        if final == "submit_plan":
            return self._done({"summary": "plan", "test_command": "", "tickets": self.tickets})
        if final == "submit_review":
            self.review_briefs.append(task.user_prompt)
            return self._done(self.review(task))
        if task.read_only:
            return AgentLoopResult(final_text="Two tickets are done.", stop_reason="completed")

        self.developer_briefs.append(task.user_prompt)
        title = task.user_prompt.split("Your ticket: ", 1)[1].split("\n", 1)[0]
        self.attempts[title] = self.attempts.get(title, 0) + 1
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            outcome = self.develop(task, self.attempts[title])
            if asyncio.iscoroutine(outcome):
                outcome = await outcome
        finally:
            self.active -= 1
        if isinstance(outcome, AgentLoopResult):
            return outcome
        return AgentLoopResult(final_text="done", stop_reason="completed", usage={"total_tokens": 10})

    @staticmethod
    def _done(payload: dict[str, Any]) -> AgentLoopResult:
        return AgentLoopResult(final_text="", stop_reason="completed", final_payload=payload)


def ticket(title: str, depends_on: list[int] | None = None) -> dict[str, Any]:
    return {"title": title, "description": f"do {title}", "acceptance_criteria": "works", "depends_on": depends_on or []}


def title_of(task: AgentTask) -> str:
    return task.user_prompt.split("Your ticket: ", 1)[1].split("\n", 1)[0]


def write_own_file(task: AgentTask, attempt: int) -> None:
    (task.workspace_root / f"{title_of(task)}.txt").write_text(f"{title_of(task)}\n", encoding="utf-8")


async def make_project(store, developers: int = 2, **fields: Any) -> DevProject:
    project = DevProject(id="prj-team", name="Team", goal="Build the thing.", engine="test", **fields)
    project.set_team(default_team(project.id, developers))
    await store.save_project(project)
    return project


def orchestrator_for(store, engine: TeamEngine, tmp_path: Path, **kwargs: Any) -> DevTeamOrchestrator:
    return DevTeamOrchestrator(
        store=store,
        engines={"test": engine, "loop": engine},
        runner=CommandRunner(allowed_commands=["python", "git"]),
        workspaces_dir=str(tmp_path),
        approval_poll_seconds=0.01,
        **{"max_rework_rounds": 1, **kwargs},
    )


async def test_two_developers_work_at_the_same_time_and_both_changes_land(tmp_path: Path):
    store = InMemoryDevProjectStore()
    both_started = asyncio.Event()

    async def develop(task: AgentTask, attempt: int) -> None:
        write_own_file(task, attempt)
        engine.started = getattr(engine, "started", 0) + 1
        if engine.started == 2:
            both_started.set()
        await asyncio.wait_for(both_started.wait(), timeout=10)  # fails unless they overlap

    engine = TeamEngine([ticket("alpha"), ticket("beta")], develop)
    project = await make_project(store)

    result = await orchestrator_for(store, engine, tmp_path).run_project(project.id)

    assert result.status == ProjectStatus.COMPLETED, result.failure_reason
    assert engine.max_active == 2
    tickets = await store.list_tickets(project.id)
    assert {t.assignee_id for t in tickets} == {None}  # released once done
    workers = {e.actor_id for e in store.events if e.kind == "ticket" and "IN_PROGRESS" in e.summary}
    assert workers == {m.id for m in project.developers()}

    workspace = ProjectWorkspace(Path(result.workspace_path))
    assert sorted(p.name for p in workspace.root.glob("*.txt")) == ["alpha.txt", "beta.txt"]
    assert sorted(c["subject"] for c in await workspace.log_since(result.base_commit)) == ["alpha", "beta"]
    assert not await workspace.has_pending_changes()
    # Worktrees and ticket branches are cleaned up
    assert not list((workspace.root.parent / f"{workspace.root.name}.worktrees").glob("*"))
    assert "agency-ticket" not in (await workspace.git("branch", "--list")).output


async def test_dependent_ticket_waits_and_sees_the_merged_work(tmp_path: Path):
    store = InMemoryDevProjectStore()
    seen: dict[str, bool] = {}

    def develop(task: AgentTask, attempt: int) -> None:
        if title_of(task) == "second":
            seen["first_is_merged"] = (task.workspace_root / "first.txt").exists()
        write_own_file(task, attempt)

    engine = TeamEngine([ticket("first"), ticket("second", depends_on=[1])], develop)
    project = await make_project(store)

    result = await orchestrator_for(store, engine, tmp_path).run_project(project.id)

    assert result.status == ProjectStatus.COMPLETED, result.failure_reason
    assert seen == {"first_is_merged": True}
    assert engine.max_active == 1  # never in parallel: the second had to wait


async def test_conflicting_changes_send_the_later_ticket_back_and_it_recovers(tmp_path: Path):
    store = InMemoryDevProjectStore()
    alpha_merged = asyncio.Event()

    async def develop(task: AgentTask, attempt: int) -> None:
        shared = task.workspace_root / "README.md"
        if title_of(task) == "alpha":
            shared.write_text("# alpha was here\n", encoding="utf-8")
            return
        if attempt == 1:
            # Edit the same line from the old base, and only finish after alpha has merged
            shared.write_text("# beta was here\n", encoding="utf-8")
            await asyncio.wait_for(alpha_merged.wait(), timeout=10)
        else:
            assert shared.read_text(encoding="utf-8") == "# alpha was here\n"  # rebuilt on latest
            shared.write_text("# alpha was here\n# and beta\n", encoding="utf-8")

    async def on_activity(event) -> None:
        if event.kind == "ticket" and "'alpha' moved to DONE" in event.summary:
            alpha_merged.set()

    engine = TeamEngine([ticket("alpha"), ticket("beta")], develop)
    project = await make_project(store)

    result = await orchestrator_for(store, engine, tmp_path, on_activity=on_activity).run_project(project.id)

    assert result.status == ProjectStatus.COMPLETED, result.failure_reason
    beta = next(t for t in await store.list_tickets(project.id) if t.title == "beta")
    assert beta.attempts == 2
    assert any("conflicts with newer work" in e.summary for e in store.events)
    retry_brief = [b for b in engine.developer_briefs if "Your ticket: beta" in b][1]
    assert "conflicted with work that was merged" in retry_brief and "beta was here" in retry_brief
    workspace = ProjectWorkspace(Path(result.workspace_path))
    assert (workspace.root / "README.md").read_text(encoding="utf-8") == "# alpha was here\n# and beta\n"


async def test_tests_are_rerun_after_combining_with_newer_work(tmp_path: Path):
    """Each change passes alone; together they break. The later one must be caught at merge."""
    store = InMemoryDevProjectStore()
    alpha_merged = asyncio.Event()
    check = "import os, sys\nsys.exit(1 if os.path.exists('a.txt') and os.path.exists('b.txt') else 0)\n"

    async def develop(task: AgentTask, attempt: int) -> None:
        (task.workspace_root / "check.py").write_text(check, encoding="utf-8")
        if title_of(task) == "alpha":
            (task.workspace_root / "a.txt").write_text("a", encoding="utf-8")
        elif attempt == 1:
            (task.workspace_root / "b.txt").write_text("b", encoding="utf-8")
            await asyncio.wait_for(alpha_merged.wait(), timeout=10)
        else:
            (task.workspace_root / "b.txt").unlink()
            (task.workspace_root / "c.txt").write_text("c", encoding="utf-8")

    async def on_activity(event) -> None:
        if event.kind == "ticket" and "'alpha' moved to DONE" in event.summary:
            alpha_merged.set()

    engine = TeamEngine([ticket("alpha"), ticket("beta")], develop)
    project = await make_project(store, test_command="python check.py")

    result = await orchestrator_for(store, engine, tmp_path, on_activity=on_activity).run_project(project.id)

    assert result.status == ProjectStatus.COMPLETED, result.failure_reason
    retry_brief = [b for b in engine.developer_briefs if "Your ticket: beta" in b][1]
    assert "After combining with newer work" in retry_brief
    workspace = ProjectWorkspace(Path(result.workspace_path))
    assert not (workspace.root / "b.txt").exists() and (workspace.root / "c.txt").exists()
    assert (await CommandRunner(allowed_commands=["python"]).run("python check.py", workspace.root)).ok


async def test_human_approval_gates_the_merge(tmp_path: Path):
    store = InMemoryDevProjectStore()
    engine = TeamEngine([ticket("alpha")], write_own_file)
    project = await make_project(store, developers=1, require_approval=True)
    orchestrator = orchestrator_for(store, engine, tmp_path)

    run = asyncio.create_task(orchestrator.run_project(project.id))
    waiting = await _wait_for_status(store, project.id, TicketStatus.AWAITING_APPROVAL)
    workspace = ProjectWorkspace(Path((await store.get_project(project.id)).workspace_path))
    assert not (workspace.root / "alpha.txt").exists()  # nothing merged before sign-off
    approval_event = next(e for e in store.events if e.summary == "waiting for your approval")
    assert "alpha.txt" in approval_event.detail["diff"]

    assert await store.set_ticket_approval(project.id, waiting.id, "REJECTED", "Use a better name.")
    await _wait_for_attempt(engine, "alpha", 2)
    assert "rejected this:\nUse a better name." in engine.developer_briefs[1]

    waiting = await _wait_for_status(store, project.id, TicketStatus.AWAITING_APPROVAL)
    assert await store.set_ticket_approval(project.id, waiting.id, "APPROVED", "")
    result = await asyncio.wait_for(run, timeout=20)

    assert result.status == ProjectStatus.COMPLETED, result.failure_reason
    assert (workspace.root / "alpha.txt").exists()
    # A decision on a ticket that is not waiting is refused
    assert not await store.set_ticket_approval(project.id, waiting.id, "APPROVED", "")


async def _wait_for_status(store, project_id: str, status: TicketStatus):
    for _ in range(1000):
        for item in await store.list_tickets(project_id):
            if item.status == status and item.approval == "":
                return item
        await asyncio.sleep(0.01)
    raise AssertionError(f"no ticket reached {status}")


async def _wait_for_attempt(engine: TeamEngine, title: str, attempt: int) -> None:
    for _ in range(1000):
        if engine.attempts.get(title, 0) >= attempt:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("developer did not retry")


async def test_guidance_reaches_every_later_brief_and_questions_do_not(tmp_path: Path):
    store = InMemoryDevProjectStore()
    engine = TeamEngine([ticket("alpha")], write_own_file)
    project = await make_project(store, developers=1)
    orchestrator = orchestrator_for(store, engine, tmp_path)
    await orchestrator.add_guidance(project.id, "Use British spelling in comments.")

    await orchestrator.run_project(project.id)
    answer = await orchestrator.answer_question(project.id, "How is it going?")

    assert "Use British spelling in comments." in engine.developer_briefs[0]
    assert "Use British spelling in comments." in engine.review_briefs[0]
    assert answer == "Two tickets are done."
    kinds = [(e.actor_role, e.kind) for e in store.events if e.kind in ("human_message", "message")]
    assert kinds == [("HUMAN", "human_message"), ("HUMAN", "human_message"), ("MANAGER", "message")]
    # The question is recorded but is not an instruction
    await orchestrator.add_guidance(project.id, "second note")
    assert "How is it going?" not in await orchestrator._guidance(project)


async def test_write_outside_the_project_discards_the_attempt(tmp_path: Path):
    store = InMemoryDevProjectStore()

    def develop(task: AgentTask, attempt: int) -> AgentLoopResult | None:
        write_own_file(task, attempt)
        if attempt == 1:
            return AgentLoopResult(
                final_text="done", stop_reason="completed", violations=["wrote outside the project: C:/elsewhere.txt"]
            )
        return None

    engine = TeamEngine([ticket("alpha")], develop)
    project = await make_project(store, developers=1)

    result = await orchestrator_for(store, engine, tmp_path).run_project(project.id)

    assert result.status == ProjectStatus.COMPLETED
    [done] = await store.list_tickets(project.id)
    assert done.attempts == 2
    assert [e.summary for e in store.events if e.kind == "violation"] == ["wrote outside the project; attempt discarded"]
    assert "Keep every change inside the project directory" in engine.developer_briefs[1]
    assert not engine.review_briefs[:-1]  # the first attempt never reached review


async def test_quota_exhaustion_pauses_then_resumes_by_itself(tmp_path: Path):
    store = InMemoryDevProjectStore()
    state = {"quota": False}

    def develop(task: AgentTask, attempt: int) -> None:
        if title_of(task) == "beta" and not state["quota"]:
            raise QuotaExhaustedError("RESOURCE_EXHAUSTED: quota exceeded")
        write_own_file(task, attempt)

    engine = TeamEngine([ticket("alpha"), ticket("beta", depends_on=[1])], develop)
    project = await make_project(store, developers=1)
    studio = StudioService(
        store=store,
        orchestrator_factory=lambda s, listener: orchestrator_for(s, engine, tmp_path, on_activity=listener),
        quota_retry_seconds=0.05,
    )

    await studio.start(project.id)
    await studio.wait(project.id)
    paused = await store.get_project(project.id)
    assert paused.status == ProjectStatus.WAITING_FOR_QUOTA
    assert "quota exceeded" in paused.failure_reason
    alpha, beta = await store.list_tickets(project.id)
    assert alpha.status == TicketStatus.DONE  # finished work is kept

    state["quota"] = True  # quota comes back; nobody calls start
    for _ in range(500):
        if (await store.get_project(project.id)).status == ProjectStatus.COMPLETED:
            break
        await asyncio.sleep(0.02)
    assert (await store.get_project(project.id)).status == ProjectStatus.COMPLETED
    assert engine.attempts["alpha"] == 1  # not redone after the wait
    await studio.shutdown()


async def test_cancel_while_waiting_for_quota_stops_the_auto_resume(tmp_path: Path):
    store = InMemoryDevProjectStore()

    def develop(task: AgentTask, attempt: int) -> None:
        raise QuotaExhaustedError("quota exceeded")

    engine = TeamEngine([ticket("alpha")], develop)
    project = await make_project(store, developers=1)
    studio = StudioService(
        store=store,
        orchestrator_factory=lambda s, listener: orchestrator_for(s, engine, tmp_path),
        quota_retry_seconds=30,
    )
    await studio.start(project.id)
    await studio.wait(project.id)
    await asyncio.sleep(0)

    assert await studio.cancel(project.id) is True
    assert (await store.get_project(project.id)).status == ProjectStatus.CANCELLED
    assert engine.attempts == {"alpha": 1}
    await studio.shutdown()


@pytest.fixture
async def api(tmp_path: Path):
    db = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'studio.db'}", echo=False)
    async with db.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(db, expire_on_commit=False)
    engine = TeamEngine([ticket("alpha"), ticket("beta")], write_own_file)
    studio = StudioService(
        store=SQLAlchemyDevProjectStore(factory),
        orchestrator_factory=lambda s, listener: orchestrator_for(s, engine, tmp_path / "ws", on_activity=listener),
        team_directory=StudioTeamDirectory(factory),
    )
    app.dependency_overrides[get_studio] = lambda: studio
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, studio, engine, factory
    app.dependency_overrides.clear()
    await studio.shutdown()
    await db.dispose()


async def create(client: AsyncClient, **fields: Any) -> dict[str, Any]:
    body = {"name": "P", "goal": "A goal long enough to pass validation.", "engine": "", "auto_start": False, **fields}
    response = await client.post("/studio/projects", json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def test_team_can_be_reshaped_before_the_project_runs(api):
    client, studio, _, _ = api
    project = await create(client, developers=1)
    base = f"/studio/projects/{project['id']}"
    team = (await client.get(base)).json()["team"]
    assert [m["role"] for m in team] == ["MANAGER", "DEVELOPER", "QA", "REVIEWER"]

    added = await client.post(f"{base}/team", json={"name": "Ada", "role": "DEVELOPER"})
    assert added.status_code == 201
    ada = next(m for m in added.json() if m["name"] == "Ada")
    renamed = await client.patch(f"{base}/team/{ada['id']}", json={"name": "Ada L."})
    assert "Ada L." in [m["name"] for m in renamed.json()]

    # A team cannot have two managers, or lose its only reviewer
    assert (await client.post(f"{base}/team", json={"name": "Boss", "role": "MANAGER"})).status_code == 422
    reviewer = next(m for m in team if m["role"] == "REVIEWER")
    assert (await client.delete(f"{base}/team/{reviewer['id']}")).status_code == 422
    assert (await client.delete(f"{base}/team/nobody")).status_code == 404

    removed = await client.delete(f"{base}/team/{ada['id']}")
    assert [m["role"] for m in removed.json()] == ["MANAGER", "DEVELOPER", "QA", "REVIEWER"]


async def test_running_project_registers_employees_and_refuses_team_changes(api):
    client, studio, engine, factory = api
    project = await create(client, developers=2, engine="loop")
    base = f"/studio/projects/{project['id']}"

    hold = asyncio.Event()
    original = engine.develop

    async def slow(task: AgentTask, attempt: int) -> None:
        await hold.wait()
        original(task, attempt)

    engine.develop = slow
    assert (await client.post(f"{base}/start")).status_code == 200
    try:
        assert (await client.post(f"{base}/team", json={"name": "Late", "role": "DEVELOPER"})).status_code == 409
    finally:
        hold.set()
    await studio.wait(project["id"])
    assert (await client.get(base)).json()["status"] == "COMPLETED"

    async with factory() as session:
        employees = (await session.execute(select(EmployeeModel))).scalars().all()
    assert sorted(e.title for e in employees) == [
        "Code Reviewer", "Engineering Manager", "QA Engineer", "Software Developer", "Software Developer",
    ]
    assert {e.status for e in employees} == {"ACTIVE"}


async def test_messages_ask_and_approval_endpoints(api):
    client, studio, engine, _ = api
    project = await create(client, developers=1, engine="loop", require_approval=True)
    base = f"/studio/projects/{project['id']}"

    assert (await client.post(f"{base}/messages", json={"text": "Prefer small functions."})).status_code == 201
    assert (await client.post(f"{base}/start")).status_code == 200

    ticket_id = None
    for _ in range(1000):
        board = (await client.get(f"{base}/board")).json()
        if board["AWAITING_APPROVAL"]:
            ticket_id = board["AWAITING_APPROVAL"][0]["id"]
            break
        await asyncio.sleep(0.01)
    assert ticket_id, "no ticket reached AWAITING_APPROVAL"
    assert "Prefer small functions." in engine.developer_briefs[0]

    done_ticket = "tkt-not-waiting"
    assert (await client.post(f"{base}/tickets/{done_ticket}/approve")).status_code == 409
    assert (await client.post(f"{base}/tickets/{ticket_id}/approve")).status_code == 200

    for _ in range(1000):
        board = (await client.get(f"{base}/board")).json()
        if board["AWAITING_APPROVAL"] and board["AWAITING_APPROVAL"][0]["id"] != ticket_id:
            await client.post(f"{base}/tickets/{board['AWAITING_APPROVAL'][0]['id']}/approve")
        if len(board["DONE"]) == 2:
            break
        await asyncio.sleep(0.01)
    await studio.wait(project["id"])
    assert (await client.get(base)).json()["status"] == "COMPLETED"

    asked = await client.post(f"{base}/ask", json={"text": "What got done?"})
    assert asked.json() == {"answer": "Two tickets are done."}


async def test_projects_cut_off_by_a_restart_are_resumed(api):
    client, studio, engine, _ = api
    project = await create(client, developers=1, engine="loop")
    stale = await studio.store.get_project(project["id"])
    stale.set_status(ProjectStatus.RUNNING)
    await studio.store.save_project(stale)

    assert await studio.recover_interrupted(resume=True) == [project["id"]]
    await studio.wait(project["id"])

    assert (await client.get(f"/studio/projects/{project['id']}")).json()["status"] == "COMPLETED"
    assert sorted(engine.attempts) == ["alpha", "beta"]
    assert TeamRole.MANAGER.value in {m["role"] for m in (await client.get(f"/studio/projects/{project['id']}")).json()["team"]}


async def test_member_can_be_renamed_while_the_team_is_working(api):
    client, studio, engine, _ = api
    project = await create(client, developers=1, engine="loop")
    base = f"/studio/projects/{project['id']}"
    developer = next(m for m in (await client.get(base)).json()["team"] if m["role"] == "DEVELOPER")

    hold = asyncio.Event()
    original = engine.develop

    async def slow(task: AgentTask, attempt: int) -> None:
        await hold.wait()
        original(task, attempt)

    engine.develop = slow
    await client.post(f"{base}/start")
    for _ in range(500):  # wait until the developer is inside a ticket
        if engine.attempts:
            break
        await asyncio.sleep(0.01)
    try:
        renamed = await client.patch(f"{base}/team/{developer['id']}", json={"name": "Kiran"})
        assert renamed.status_code == 200, renamed.text
    finally:
        hold.set()
    await studio.wait(project["id"])

    detail = (await client.get(base)).json()
    assert detail["status"] == "COMPLETED"
    # The run saved the project many times after the rename and did not put the old name back
    assert "Kiran" in [m["name"] for m in detail["team"]]
    assert developer["name"] not in [m["name"] for m in detail["team"]]
    events = (await client.get(f"{base}/events")).json()
    assert "Kiran" in {e["actor_name"] for e in events if e["actor_role"] == "DEVELOPER"}


async def test_delete_project_keeps_the_code_unless_asked(api, tmp_path, monkeypatch):
    from src.infrastructure.config import settings

    monkeypatch.setattr(settings, "STUDIO_WORKSPACES_DIR", str(tmp_path / "ws"))
    client, studio, engine, _ = api

    kept = await create(client, developers=1, engine="loop")
    hold = asyncio.Event()
    original = engine.develop

    async def slow(task: AgentTask, attempt: int) -> None:
        await hold.wait()
        original(task, attempt)

    engine.develop = slow
    await client.post(f"/studio/projects/{kept['id']}/start")
    try:
        running = await client.delete(f"/studio/projects/{kept['id']}")
        assert running.status_code == 409  # must be stopped first
    finally:
        hold.set()
    await studio.wait(kept["id"])
    workspace = Path((await client.get(f"/studio/projects/{kept['id']}")).json()["workspace_path"])
    assert (workspace / "alpha.txt").exists()

    assert (await client.delete(f"/studio/projects/{kept['id']}")).status_code == 204
    assert (await client.get(f"/studio/projects/{kept['id']}")).status_code == 404
    assert await studio.store.list_tickets(kept["id"]) == []
    assert await studio.store.list_events(kept["id"]) == []
    assert (workspace / "alpha.txt").exists()  # the team's code is still on disk

    engine.develop = original
    engine.attempts.clear()
    removed = await create(client, developers=1, engine="loop")
    await client.post(f"/studio/projects/{removed['id']}/start")
    await studio.wait(removed["id"])
    second = Path((await client.get(f"/studio/projects/{removed['id']}")).json()["workspace_path"])
    assert second.is_dir()

    gone = await client.delete(f"/studio/projects/{removed['id']}", params={"remove_workspace": "true"})
    assert gone.status_code == 204
    assert not second.exists()
    assert workspace.exists()  # only the deleted project's folder went
    assert (await client.get("/studio/projects")).json() == []


def test_workspace_removal_refuses_paths_outside_the_studio_folder(tmp_path, monkeypatch):
    from src.application.studio_service import _remove_workspace
    from src.infrastructure.config import settings

    monkeypatch.setattr(settings, "STUDIO_WORKSPACES_DIR", str(tmp_path / "ws"))
    outside = tmp_path / "important"
    outside.mkdir()
    (outside / "keep.txt").write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="not a studio workspace"):
        _remove_workspace(outside)
    with pytest.raises(ValueError, match="not a studio workspace"):
        _remove_workspace(tmp_path / "ws")  # the studio folder itself is not a project
    assert (outside / "keep.txt").exists()
