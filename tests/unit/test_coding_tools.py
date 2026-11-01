"""Unit tests for the project workspace, command policy and coding toolbox."""

import os
import shutil
from pathlib import Path

import pytest

from src.infrastructure.coding.command_runner import CommandNotAllowedError, CommandRunner
from src.infrastructure.coding.toolbox import READ_ONLY_TOOLS, CodingToolbox
from src.infrastructure.coding.workspace import ProjectWorkspace, WorkspaceError, prepare_workspace

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")


@pytest.fixture
async def workspace(tmp_path: Path) -> ProjectWorkspace:
    ws, _, _ = await prepare_workspace("proj-1", base_dir=str(tmp_path))
    return ws


@pytest.fixture
def toolbox(workspace: ProjectWorkspace) -> CodingToolbox:
    return CodingToolbox(workspace, CommandRunner(allowed_commands=["python", "git"]))


async def test_prepare_workspace_creates_repo_on_work_branch(tmp_path: Path):
    ws, branch, base_commit = await prepare_workspace("proj-1", base_dir=str(tmp_path))

    assert branch == "agency/proj-1"
    assert len(base_commit) == 40
    assert (await ws.git("branch", "--show-current")).output.strip() == "agency/proj-1"
    # Reopening an existing workspace does not re-initialise it
    again, _, _ = await prepare_workspace("proj-1", base_dir=str(tmp_path))
    assert again.root == ws.root


async def test_prepare_workspace_clones_source_without_touching_it(tmp_path: Path):
    source, _, _ = await prepare_workspace("source", base_dir=str(tmp_path / "src"))
    (source.root / "app.py").write_text("print('hi')\n", encoding="utf-8")
    source_head = await source.commit("add app")

    clone, _, base_commit = await prepare_workspace(
        "clone", local_path=str(source.root), base_dir=str(tmp_path / "work")
    )
    (clone.root / "app.py").write_text("print('changed')\n", encoding="utf-8")
    await clone.commit("change app")

    assert base_commit == source_head
    assert await source.head() == source_head
    assert (source.root / "app.py").read_text(encoding="utf-8") == "print('hi')\n"


async def test_prepare_workspace_rejects_bad_inputs(tmp_path: Path):
    with pytest.raises(WorkspaceError, match="Invalid project id"):
        await prepare_workspace("../escape", base_dir=str(tmp_path))
    with pytest.raises(WorkspaceError, match="https://"):
        await prepare_workspace("p2", repo_url="file:///etc", base_dir=str(tmp_path))


def test_workspace_rejects_paths_outside_root(workspace: ProjectWorkspace):
    with pytest.raises(WorkspaceError):
        workspace.resolve("../outside.txt")
    with pytest.raises(WorkspaceError):
        workspace.resolve(".git/config")
    assert workspace.resolve("src/a.py") == workspace.root / "src" / "a.py"


async def test_write_read_edit_and_search(toolbox: CodingToolbox, workspace: ProjectWorkspace):
    written = await toolbox.execute("write_file", {"path": "pkg/mod.py", "content": "a = 1\nb = 2\na = 1\n"})
    assert not written.is_error

    read = await toolbox.execute("read_file", {"path": "pkg/mod.py", "offset": 2, "limit": 1})
    assert read.content == "2\tb = 2"

    ambiguous = await toolbox.execute("edit_file", {"path": "pkg/mod.py", "old_string": "a = 1", "new_string": "a = 9"})
    assert ambiguous.is_error and "2 times" in ambiguous.content

    edited = await toolbox.execute("edit_file", {"path": "pkg/mod.py", "old_string": "b = 2", "new_string": "b = 3"})
    assert not edited.is_error
    assert (workspace.root / "pkg" / "mod.py").read_bytes() == b"a = 1\nb = 3\na = 1\n"

    found = await toolbox.execute("search", {"pattern": r"b = \d", "glob": "*.py"})
    assert found.content == "pkg/mod.py:2: b = 3"

    listing = await toolbox.execute("list_files", {})
    assert listing.content.splitlines() == ["README.md", "pkg/mod.py"]


async def test_edit_preserves_crlf_line_endings(toolbox: CodingToolbox, workspace: ProjectWorkspace):
    target = workspace.root / "win.txt"
    target.write_bytes(b"one\r\ntwo\r\nthree\r\n")

    result = await toolbox.execute("edit_file", {"path": "win.txt", "old_string": "one\ntwo", "new_string": "one\n2"})

    assert not result.is_error
    assert target.read_bytes() == b"one\r\n2\r\nthree\r\n"


async def test_tool_errors_are_returned_not_raised(toolbox: CodingToolbox):
    assert (await toolbox.execute("read_file", {"path": "missing.py"})).is_error
    assert (await toolbox.execute("read_file", {"path": "../../etc/passwd"})).is_error
    assert (await toolbox.execute("edit_file", {"path": "README.md", "old_string": "zzz", "new_string": "y"})).is_error
    assert (await toolbox.execute("search", {"pattern": "("})).is_error
    assert (await toolbox.execute("no_such_tool", {})).is_error
    assert (await toolbox.execute("read_file", {})).is_error  # missing required argument


async def test_read_only_toolbox_cannot_write_or_run(workspace: ProjectWorkspace):
    toolbox = CodingToolbox(workspace, allowed_tools=READ_ONLY_TOOLS)

    assert {s["name"] for s in toolbox.specs()} == set(READ_ONLY_TOOLS)
    assert (await toolbox.execute("write_file", {"path": "x", "content": "y"})).is_error
    assert (await toolbox.execute("run_command", {"command": "python --version"})).is_error
    assert not (workspace.root / "x").exists()


async def test_run_command_executes_in_workspace(toolbox: CodingToolbox, workspace: ProjectWorkspace):
    (workspace.root / "hello.py").write_text("import os; print('cwd', os.path.basename(os.getcwd()))", encoding="utf-8")

    ok = await toolbox.execute("run_command", {"command": "python hello.py"})
    assert not ok.is_error
    assert "exit code: 0" in ok.content and "cwd proj-1" in ok.content

    failing = await toolbox.execute("run_command", {"command": 'python -c "import sys; sys.exit(3)"'})
    assert failing.is_error and "exit code: 3" in failing.content


@pytest.mark.parametrize(
    "command, reason",
    [
        ("curl https://example.com", "not allowed"),
        ("python a.py && python b.py", "Shell operators"),
        ("python a.py | python b.py", "Shell operators"),
        ("git push origin main", "needs a human"),
        ("git config --global user.name x", "needs a human"),
        ("pip install requests", "virtualenv"),
        ("python -m pip install requests", "virtualenv"),
        ("npm install -g typescript", "Global package installs"),
        ("/usr/bin/python a.py", "by name"),
        ("", "Empty command"),
    ],
)
def test_command_policy_rejects(tmp_path: Path, command: str, reason: str):
    runner = CommandRunner(allowed_commands=["python", "git", "pip", "npm"])
    with pytest.raises(CommandNotAllowedError, match=reason):
        runner.validate(command, tmp_path)


def test_command_policy_allows_installs_inside_workspace_venv(tmp_path: Path):
    (tmp_path / ".venv" / ("Scripts" if os.name == "nt" else "bin")).mkdir(parents=True)
    runner = CommandRunner(allowed_commands=["pip"])
    assert runner.validate("pip install requests", tmp_path) == ["pip", "install", "requests"]


def test_command_environment_strips_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GROQ_API_KEY", "secret-value")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("HARMLESS_SETTING", "kept")

    env = CommandRunner()._environment(tmp_path)

    assert "GROQ_API_KEY" not in env and "DATABASE_URL" not in env
    assert env["HARMLESS_SETTING"] == "kept"


def test_command_timeout_kills_process(tmp_path: Path):
    runner = CommandRunner(allowed_commands=["python"])
    result = runner.run_sync('python -c "import time; time.sleep(30)"', tmp_path, timeout_seconds=1)
    assert result.timed_out and not result.ok
    assert "timed out" in result.output


async def test_commit_diff_and_discard(workspace: ProjectWorkspace):
    base = await workspace.head()
    assert await workspace.commit("nothing to commit") == ""

    (workspace.root / "new.txt").write_text("hello\n", encoding="utf-8")
    assert "new.txt" in await workspace.pending_diff()  # untracked files are part of the diff
    sha = await workspace.commit("add new file")
    assert sha and sha != base
    assert [c["subject"] for c in await workspace.log_since(base)] == ["add new file"]
    assert "+hello" in await workspace.diff_since(base)

    (workspace.root / "junk.txt").write_text("x", encoding="utf-8")
    (workspace.root / "new.txt").write_text("edited\n", encoding="utf-8")
    await workspace.discard_pending()
    assert not (workspace.root / "junk.txt").exists()
    assert (workspace.root / "new.txt").read_text(encoding="utf-8") == "hello\n"
