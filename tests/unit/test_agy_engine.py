"""Unit tests for the Antigravity CLI engine, run against a scripted stand-in for the CLI."""

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

from src.application.agent_engine import AgentTask
from src.application.dev_team_service import (
    SUBMIT_REVIEW_TOOL,
    DevTeamOrchestrator,
    InMemoryDevProjectStore,
)
from src.domain.dev_project import DevProject, TeamRole
from src.domain.exceptions import CancellationError, ConfigurationError, ModelExecutionError
from src.infrastructure.coding.agy_engine import AgyEngine
from src.infrastructure.config import settings

FAKE_AGY = [sys.executable, str(Path(__file__).parent.parent / "fixtures" / "fake_agy.py")]


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    return root


@pytest.fixture
def record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "record.json"
    monkeypatch.setenv("FAKE_AGY_RECORD", str(path))
    return path


def scenario(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    monkeypatch.setenv("FAKE_AGY_SCENARIO", name)


def task(workspace: Path, **overrides: Any) -> AgentTask:
    return AgentTask(system_prompt="You are a developer.", user_prompt="Add the feature.", workspace_root=workspace, **overrides)


async def run(engine: AgyEngine, agent_task: AgentTask, model: str = "gemini-test", **kwargs: Any):
    events: list[dict[str, Any]] = []

    async def sink(event: dict[str, Any]) -> None:
        events.append(event)

    result = await engine.run(agent_task, provider="", model=model, on_event=sink, **kwargs)
    return result, events


async def test_editing_run_invokes_cli_correctly_and_streams_activity(workspace, record, monkeypatch):
    scenario(monkeypatch, "edit")
    monkeypatch.setenv("GROQ_API_KEY", "must-not-leak")

    result, events = await run(AgyEngine(command=FAKE_AGY), task(workspace))

    assert result.completed
    assert result.final_text == "Added feature.py."
    assert result.usage == {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
    assert result.tool_calls == 2
    assert (workspace / "feature.py").read_text(encoding="utf-8") == "VALUE = 1\n"
    assert [e["summary"] for e in events if e["type"] == "tool_call"] == ["reading README.md", "writing feature.py"]

    seen = json.loads(record.read_text(encoding="utf-8"))
    argv = seen["argv"]
    assert Path(seen["cwd"]) == workspace
    assert argv[argv.index("--model") + 1] == "gemini-test"
    assert argv[argv.index("--mode") + 1] == "accept-edits"
    assert argv[argv.index("--output-format") + 1] == "stream-json"
    assert str(workspace) in [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
    assert "--dangerously-skip-permissions" not in argv
    assert "--json-schema" not in argv
    assert seen["env_has_secret"] is False
    # The brief carries both prompts and tells the agent it cannot run commands
    assert "You are a developer." in seen["brief"] and "Add the feature." in seen["brief"]
    assert "You cannot run commands here" in seen["brief"]


async def test_brief_file_is_removed_after_the_run(workspace, record, monkeypatch):
    scenario(monkeypatch, "edit")
    await run(AgyEngine(command=FAKE_AGY), task(workspace))

    prompt = next(a for a in json.loads(record.read_text(encoding="utf-8"))["argv"] if a.startswith("-p="))
    brief_path = Path(prompt.split("Read the file ", 1)[1].split(" and carry out", 1)[0])
    assert not brief_path.parent.exists()
    assert not list(workspace.glob("brief*"))  # and it never lived in the project


async def test_read_only_role_gets_no_edit_mode_and_a_schema(workspace, record, monkeypatch):
    scenario(monkeypatch, "structured")

    result, _ = await run(AgyEngine(command=FAKE_AGY), task(workspace, read_only=True, final_tool=SUBMIT_REVIEW_TOOL))

    assert result.final_payload == {"approved": True, "feedback": "Looks right."}  # agy's extra keys dropped
    seen = json.loads(record.read_text(encoding="utf-8"))
    assert "--mode" not in seen["argv"]
    assert json.loads(seen["argv"][seen["argv"].index("--json-schema") + 1]) == SUBMIT_REVIEW_TOOL["parameters"]
    assert "You may only read" in seen["brief"]
    assert "Ignore any instruction above to call a tool named submit_review" in seen["brief"]


async def test_denied_command_keeps_the_edits_and_is_reported(workspace, record, monkeypatch):
    scenario(monkeypatch, "denied_command")

    result, events = await run(AgyEngine(command=FAKE_AGY), task(workspace))

    assert result.completed  # the edits made before the denial still count
    assert (workspace / "feature.py").exists()
    assert "denied action: command" in result.final_text
    errors = [e for e in events if e["type"] == "tool_result" and e["is_error"]]
    assert errors[0]["summary"] == "running pytest -q"
    assert "permission check failed" in errors[0]["preview"]


async def test_quota_error_retries_once_on_the_fallback_model(workspace, record, monkeypatch):
    scenario(monkeypatch, "quota_then_ok")

    result, events = await run(AgyEngine(command=FAKE_AGY, fallback_model="fallback-model"), task(workspace))

    assert result.final_text == "answered by fallback-model"
    assert any("switching to fallback-model" in e.get("summary", "") for e in events)


async def test_quota_error_without_fallback_is_raised(workspace, record, monkeypatch):
    scenario(monkeypatch, "quota_then_ok")
    with pytest.raises(ModelExecutionError, match="RESOURCE_EXHAUSTED"):
        await run(AgyEngine(command=FAKE_AGY, fallback_model=""), task(workspace))


async def test_failed_and_crashed_runs_raise(workspace, record, monkeypatch):
    scenario(monkeypatch, "error")
    with pytest.raises(ModelExecutionError, match="something broke"):
        await run(AgyEngine(command=FAKE_AGY, fallback_model=""), task(workspace))

    scenario(monkeypatch, "crash")
    with pytest.raises(ModelExecutionError, match="without a result.*not signed in"):
        await run(AgyEngine(command=FAKE_AGY, fallback_model=""), task(workspace))


async def test_cancellation_kills_the_cli(workspace, record, monkeypatch):
    scenario(monkeypatch, "hang")
    seen_events = 0

    def cancel_after_first_event() -> bool:
        return seen_events > 0

    async def sink(event: dict[str, Any]) -> None:
        nonlocal seen_events
        seen_events += 1

    with pytest.raises(CancellationError):
        await AgyEngine(command=FAKE_AGY).run(
            task(workspace), provider="", model="m", on_event=sink, should_cancel=cancel_after_first_event
        )


async def test_write_outside_the_project_is_flagged(workspace, record, monkeypatch):
    scenario(monkeypatch, "outside")

    _, events = await run(AgyEngine(command=FAKE_AGY), task(workspace))

    flagged = [e for e in events if e["type"] == "tool_result"]
    assert flagged[0]["summary"] == "writing outside the project"
    assert flagged[0]["preview"].endswith("elsewhere.txt")


async def test_missing_cli_is_a_configuration_error(workspace):
    with pytest.raises(ConfigurationError, match="not found on PATH"):
        await AgyEngine(command=["definitely-not-installed-agy"]).run(task(workspace), provider="", model="m")


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
async def test_orchestrator_routes_roles_to_engine_with_per_role_models(tmp_path: Path):
    calls: list[tuple[str, bool, str | None]] = []

    class RecordingEngine:
        async def run(self, agent_task: AgentTask, *, provider, model, on_event=None, should_cancel=None):
            from src.application.agent_loop import AgentLoopResult

            final = agent_task.final_tool["name"] if agent_task.final_tool else None
            calls.append((model, agent_task.read_only, final))
            if final == "submit_plan":
                payload = {"summary": "s", "test_command": "", "tickets": [{"title": "T", "description": "d"}]}
            elif final == "submit_review":
                payload = {"approved": True, "feedback": "ok"}
            else:
                (agent_task.workspace_root / "x.txt").write_text("x", encoding="utf-8")
                payload = None
            return AgentLoopResult(final_text="done", stop_reason="completed", final_payload=payload)

    store = InMemoryDevProjectStore()
    project = DevProject(id="prj-agy", name="P", goal="Do the thing.", engine="agy")
    await store.save_project(project)
    orchestrator = DevTeamOrchestrator(store=store, engines={"agy": RecordingEngine()}, workspaces_dir=str(tmp_path))

    result = await orchestrator.run_project(project.id)

    assert result.status.value == "COMPLETED", result.failure_reason
    assert calls == [
        (settings.AGY_MODEL_MANAGER, True, "submit_plan"),
        (settings.AGY_MODEL_DEVELOPER, False, None),
        (settings.AGY_MODEL_REVIEWER, True, "submit_review"),
    ]
    assert DevTeamOrchestrator._model_for(DevProject(id="p", name="n", goal="g", model="one-model"), project.member(TeamRole.REVIEWER), "agy") == "one-model"


async def test_unknown_engine_fails_the_project_with_a_clear_reason(tmp_path: Path):
    if shutil.which("git") is None:
        pytest.skip("git is required")
    store = InMemoryDevProjectStore()
    project = DevProject(id="prj-bad", name="P", goal="Do the thing.", engine="nope")
    await store.save_project(project)

    result = await DevTeamOrchestrator(store=store, workspaces_dir=str(tmp_path)).run_project(project.id)

    assert result.status.value == "FAILED"
    assert "Unknown studio engine 'nope'" in (result.failure_reason or "")
