"""
Project workspace: a git working tree on disk that a dev team's agents work inside.
"""

import asyncio
import re
import shutil
import subprocess
from pathlib import Path

from src.infrastructure.coding.command_runner import CommandResult, CommandRunner
from src.infrastructure.config import settings

SNAPSHOT_IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}
GENERATED_FOLDERS = [
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".env",
    ".next/",
    "dist/",
    "build/",
]
AGENT_GIT_IDENTITY = ["-c", "user.name=Agency Dev Team", "-c", "user.email=agents@agency.local"]


class WorkspaceError(Exception):
    """Raised when a workspace cannot be prepared or a path escapes it."""


class ProjectWorkspace:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        # Humans set this workspace up, so git here is not bound by the agents' command policy
        self._git_runner = CommandRunner(allowed_commands=["git"], timeout_seconds=300)

    # ------------------------------------------------------------------ paths
    def resolve(self, relative_path: str) -> Path:
        """Resolve a path inside the workspace, rejecting traversal and .git internals."""
        target = (self.root / relative_path).resolve()
        try:
            relative = target.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError(f"Path '{relative_path}' is outside the project workspace.") from exc
        if relative.parts and relative.parts[0] == ".git":
            raise WorkspaceError("The .git directory is managed through the git tools.")
        return target

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    # -------------------------------------------------------------------- git
    async def git(self, *args: str, timeout_seconds: int | None = None) -> CommandResult:
        argv = ["git", *args]
        command = " ".join(argv)
        return await asyncio.to_thread(self._run_git, argv, command, timeout_seconds)

    def _run_git(self, argv: list[str], command: str, timeout_seconds: int | None) -> CommandResult:
        git = shutil.which("git")
        if git is None:
            return CommandResult(command, 127, "git is not installed on this machine.")
        completed = subprocess.run(  # noqa: S603 - fixed executable, argv list, no shell
            [git, *argv[1:]],
            cwd=str(self.root),
            capture_output=True,
            timeout=timeout_seconds or 300,
            check=False,
            env=self._git_runner._environment(self.root),
        )
        output = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
        return CommandResult(command, completed.returncode, output)

    async def head(self) -> str:
        result = await self.git("rev-parse", "HEAD")
        return result.output.strip() if result.ok else ""

    async def status(self) -> str:
        return (await self.git("status", "--short")).output

    async def pending_diff(self, max_chars: int = 40_000) -> str:
        """Diff of everything not yet committed, including new files."""
        await self.git("add", "-A")
        diff = (await self.git("diff", "--cached")).output
        if len(diff) > max_chars:
            diff = diff[:max_chars] + "\n...[diff truncated]"
        return diff

    async def diff_from_fork(self, branch: str, max_chars: int = 40_000) -> str:
        """
        Everything this worktree adds relative to where it forked from `branch`: its commits
        plus uncommitted work, but not changes other tickets merged into `branch` since.
        """
        await self.git("add", "-A")
        await self.git("rm", "--cached", "--ignore-unmatch", ".env")
        fork = (await self.git("merge-base", "HEAD", branch)).output.strip()
        diff = (await self.git(
            "diff", "--cached", fork or branch,
            "--", ".",
            ":(exclude)package-lock.json",
            ":(exclude)yarn.lock",
            ":(exclude)pnpm-lock.yaml",
            ":(exclude)Cargo.lock",
            ":(exclude)poetry.lock",
        )).output
        if len(diff) > max_chars:
            diff = diff[:max_chars] + "\n...[diff truncated]"
        return diff

    async def has_pending_changes(self) -> bool:
        return bool((await self.status()).strip())

    async def commit(self, message: str) -> str:
        """Commit all pending changes and return the new commit sha ('' if nothing to commit)."""
        if not await self.has_pending_changes():
            return ""
        await self.git("add", "-A")
        await self.git("rm", "--cached", "--ignore-unmatch", ".env")
        result = await self.git(*AGENT_GIT_IDENTITY, "commit", "-m", message)
        if not result.ok:
            raise WorkspaceError(f"git commit failed: {result.output[-500:]}")
        return await self.head()

    async def discard_pending(self) -> None:
        await self.git("reset", "--hard", "HEAD")
        await self.git("clean", "-fd")

    async def diff_since(self, base_commit: str, max_chars: int = 200_000) -> str:
        diff = (await self.git("diff", f"{base_commit}..HEAD")).output if base_commit else ""
        return diff[:max_chars]

    async def exclude_generated_folders(self) -> None:
        """
        Keep installed dependencies and caches out of every commit, whatever the project's own
        .gitignore says. Written to the repository's local exclude file, which all of its
        worktrees share and which is never committed.
        """
        git_dir = (await self.git("rev-parse", "--git-common-dir")).output.strip()
        if not git_dir:
            return
        exclude = (self.root / git_dir).resolve() / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        missing = [entry for entry in GENERATED_FOLDERS if entry not in existing.splitlines()]
        if missing:
            exclude.write_text(existing.rstrip("\n") + "\n" + "\n".join(missing) + "\n", encoding="utf-8")

    # -------------------------------------------------------------- worktrees
    async def add_worktree(self, path: Path, branch: str, start_point: str) -> "ProjectWorkspace":
        """Check out a new branch in its own directory so several agents can work at once."""
        await self.remove_worktree(path, branch)
        path.parent.mkdir(parents=True, exist_ok=True)
        result = await self.git("worktree", "add", "-b", branch, str(path), start_point)
        if not result.ok:
            raise WorkspaceError(f"git worktree add failed: {result.output[-500:]}")
        return ProjectWorkspace(path)

    async def remove_worktree(self, path: Path, branch: str) -> None:
        if path.exists():
            await self.git("worktree", "remove", "--force", str(path))
            shutil.rmtree(path, ignore_errors=True)
        await self.git("worktree", "prune")
        await self.git("branch", "-D", branch)
        try:
            path.parent.rmdir()  # drop the worktrees folder once the last one is gone
        except OSError:
            pass

    async def rebase_onto(self, branch: str) -> bool:
        """Replay this worktree's commits on top of `branch`. False (and no change) on conflict."""
        result = await self.git(*AGENT_GIT_IDENTITY, "rebase", branch)
        if result.ok:
            return True
        await self.git("rebase", "--abort")
        return False

    async def reset_to(self, ref: str) -> None:
        await self.git("reset", "--hard", ref)
        await self.git("clean", "-fd")

    async def merge_fast_forward(self, branch: str) -> None:
        result = await self.git("merge", "--ff-only", branch)
        if not result.ok:
            raise WorkspaceError(f"Could not fast-forward to '{branch}': {result.output[-500:]}")

    async def rev(self, ref: str) -> str:
        result = await self.git("rev-parse", ref)
        return result.output.strip() if result.ok else ""

    # --------------------------------------------------------------- snapshot
    def snapshot(self, max_chars: int = 12_000, max_files: int = 150) -> str:
        """
        A compact picture of the repository for an agent's brief: the file list, plus the
        contents of small text files while the budget lasts. Every exploration step an agent
        does not have to take is a model call saved.
        """
        files: list[Path] = []
        stack = [self.root]
        while stack:
            current = stack.pop()
            for entry in sorted(current.iterdir(), key=lambda p: p.name):
                if entry.is_dir():
                    if entry.name not in SNAPSHOT_IGNORED_DIRS:
                        stack.append(entry)
                elif entry.is_file() and entry.name != ".git":
                    files.append(entry)
        files.sort(key=lambda p: p.as_posix())

        listing = [self.relative(f) for f in files[:max_files]]
        if len(files) > max_files:
            listing.append(f"...and {len(files) - max_files} more files")
        parts = ["Files:\n" + "\n".join(listing or ["(empty repository)"])]

        budget = max_chars - len(parts[0])
        for file in sorted(files[:max_files], key=lambda p: p.stat().st_size):
            if file.stat().st_size > 6_000 or budget <= 0:
                break
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            block = f"\n--- {self.relative(file)} ---\n{text}"
            if len(block) > budget:
                break
            parts.append(block)
            budget -= len(block)
        return "".join(parts)

    async def log_since(self, base_commit: str) -> list[dict[str, str]]:
        revision = f"{base_commit}..HEAD" if base_commit else "HEAD"
        result = await self.git("log", revision, "--pretty=format:%H%x09%s")
        if not result.ok:
            return []
        commits = []
        for line in result.output.splitlines():
            sha, _, subject = line.partition("\t")
            if sha:
                commits.append({"sha": sha, "subject": subject})
        return commits


def _safe_dirname(project_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", project_id):
        raise WorkspaceError(f"Invalid project id '{project_id}'.")
    return project_id


async def prepare_workspace(
    project_id: str,
    repo_url: str | None = None,
    local_path: str | None = None,
    base_dir: str | None = None,
) -> tuple[ProjectWorkspace, str, str]:
    """
    Create the working tree for a project and return (workspace, branch, base_commit).

    A source repository is cloned (the original is never modified); with no source a fresh
    repository is initialised. Work happens on a dedicated branch.
    """
    base = Path(base_dir or settings.STUDIO_WORKSPACES_DIR).resolve()
    base.mkdir(parents=True, exist_ok=True)
    root = base / _safe_dirname(project_id)
    branch = f"agency/{project_id}"

    if (root / ".git").is_dir():
        workspace = ProjectWorkspace(root)
        return workspace, branch, await workspace.head()
    if root.exists() and any(root.iterdir()):
        raise WorkspaceError(f"Workspace directory '{root}' already exists and is not a git repository.")

    source = repo_url or local_path
    if source:
        if repo_url and not repo_url.startswith("https://"):
            raise WorkspaceError("Only https:// repository URLs are supported.")
        if local_path and not (Path(local_path) / ".git").exists():
            raise WorkspaceError(f"'{local_path}' is not a git repository.")
        root.parent.mkdir(parents=True, exist_ok=True)
        cloner = ProjectWorkspace(base)
        result = await cloner.git("clone", "--", source, str(root), timeout_seconds=600)
        if not result.ok:
            raise WorkspaceError(f"git clone failed: {result.output[-500:]}")
        workspace = ProjectWorkspace(root)
    else:
        root.mkdir(parents=True, exist_ok=True)
        workspace = ProjectWorkspace(root)
        await workspace.git("init")
        (root / "README.md").write_text("# New project\n", encoding="utf-8")
        await workspace.git("add", "-A")
        result = await workspace.git(*AGENT_GIT_IDENTITY, "commit", "-m", "Initial commit")
        if not result.ok:
            raise WorkspaceError(f"Could not create initial commit: {result.output[-500:]}")

    base_commit = await workspace.head()
    result = await workspace.git("checkout", "-b", branch)
    if not result.ok:
        raise WorkspaceError(f"Could not create branch '{branch}': {result.output[-500:]}")
    return workspace, branch, base_commit
