"""
Studio service: creates dev projects and runs their teams as background tasks.

Runs are in-process asyncio tasks owned by the API process. If that process stops, its
projects are restarted on the next start (finished tickets are kept, unfinished ones start
over). A project that runs out of model quota waits and resumes by itself.
"""

import asyncio
import logging
import os
import shutil
import stat
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from src.application.dev_team_service import ActivityListener, DevProjectStore, DevTeamOrchestrator
from src.domain.dev_project import (
    ACTIVE_PROJECT_STATUSES,
    DevProject,
    ProjectStatus,
    TeamMember,
    TeamRole,
    TicketStatus,
    default_team,
    validate_team,
)
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

OrchestratorFactory = Callable[[DevProjectStore, ActivityListener | None], DevTeamOrchestrator]

_ACTIVE_TICKET_STATES = {
    TicketStatus.IN_PROGRESS: "WORKING",
    TicketStatus.TESTING: "WORKING",
    TicketStatus.IN_REVIEW: "REVIEWING",
}


class ProjectAlreadyRunningError(Exception):
    pass


def _remove_workspace(path: Path) -> None:
    """Remove a project's working copy, but only if it really is inside the studio folder."""
    root = Path(settings.STUDIO_WORKSPACES_DIR).resolve()
    target = path.resolve()
    if root not in target.parents or not target.is_dir():
        raise ValueError(f"Refusing to delete '{target}': it is not a studio workspace.")

    def make_writable(function: Any, failed_path: str, _error: Any) -> None:
        os.chmod(failed_path, stat.S_IWRITE)  # git marks its object files read-only
        function(failed_path)

    shutil.rmtree(target, onerror=make_writable)
    shutil.rmtree(target.parent / f"{target.name}.worktrees", ignore_errors=True)


class TeamDirectory(Protocol):
    async def register(self, project: DevProject, provider: str, model: str) -> None: ...


def _default_orchestrator(
    store: DevProjectStore, on_activity: ActivityListener | None
) -> DevTeamOrchestrator:
    return DevTeamOrchestrator(store=store, on_activity=on_activity)


class StudioService:
    def __init__(
        self,
        store: DevProjectStore,
        on_activity: ActivityListener | None = None,
        orchestrator_factory: OrchestratorFactory = _default_orchestrator,
        team_directory: TeamDirectory | None = None,
        quota_retry_seconds: float | None = None,
    ) -> None:
        self.store = store
        self.on_activity = on_activity
        self.orchestrator_factory = orchestrator_factory
        self.team_directory = team_directory
        self.quota_retry_seconds = (
            quota_retry_seconds
            if quota_retry_seconds is not None
            else settings.STUDIO_QUOTA_RETRY_MINUTES * 60
        )
        self._tasks: dict[str, asyncio.Task[DevProject]] = {}
        self._retries: dict[str, asyncio.Task[None]] = {}
        self._cancelled: set[str] = set()

    # ---------------------------------------------------------------- create
    async def create_project(
        self,
        name: str,
        goal: str,
        tenant_id: str | None = None,
        repo_url: str | None = None,
        local_path: str | None = None,
        test_command: str | None = None,
        engine: str = "",
        provider: str = "",
        model: str = "",
        developers: int | None = None,
        require_approval: bool = False,
        created_by: str | None = None,
    ) -> DevProject:
        project = DevProject(
            id=f"prj-{uuid.uuid4().hex[:12]}",
            name=name,
            goal=goal,
            tenant_id=tenant_id,
            repo_url=repo_url,
            local_path=local_path,
            test_command=test_command,
            engine=engine,
            provider=provider,
            model=model,
            require_approval=require_approval,
            created_by=created_by,
        )
        project.set_team(default_team(project.id, developers or settings.STUDIO_DEVELOPERS))
        await self.store.save_project(project)
        return project

    # ------------------------------------------------------------------ team
    async def _editable(self, project_id: str) -> DevProject:
        project = await self.store.get_project(project_id)
        if project is None:
            raise ValueError(f"Dev project '{project_id}' not found.")
        if self.is_running(project_id):
            raise ProjectAlreadyRunningError("The team can only be changed while the project is not running.")
        return project

    async def add_member(self, project_id: str, name: str, role: TeamRole) -> DevProject:
        project = await self._editable(project_id)
        members = project.team()
        members.append(TeamMember(id=f"{project.id}-{role.value.lower()}-{uuid.uuid4().hex[:6]}", name=name, role=role))
        project.set_team(members)  # validates role counts
        await self.store.set_members(project.id, project.members)
        return project

    async def rename_member(self, project_id: str, member_id: str, name: str) -> DevProject:
        """Renaming is allowed while the team works: it changes no one's job."""
        project = await self.store.get_project(project_id)
        if project is None:
            raise ValueError(f"Dev project '{project_id}' not found.")
        members = project.team()
        target = next((m for m in members if m.id == member_id), None)
        if target is None:
            raise ValueError(f"Team member '{member_id}' not found.")
        target.name = name.strip()
        project.set_team(members)
        await self.store.set_members(project.id, project.members)
        return project

    async def remove_member(self, project_id: str, member_id: str) -> DevProject:
        project = await self._editable(project_id)
        members = project.team()
        if not any(m.id == member_id for m in members):
            raise ValueError(f"Team member '{member_id}' not found.")
        project.set_team([m for m in members if m.id != member_id])
        await self.store.set_members(project.id, project.members)
        return project

    async def delete_project(self, project_id: str, remove_workspace: bool = False) -> None:
        """
        Delete a stopped project: its record, tickets and activity. The code the team wrote
        stays on disk unless remove_workspace is set.
        """
        project = await self._editable(project_id)
        self._drop_retry(project_id)
        if remove_workspace and project.workspace_path:
            await asyncio.to_thread(_remove_workspace, Path(project.workspace_path))
        await self.store.delete_project(project_id)

    # ------------------------------------------------------------------- run
    def is_running(self, project_id: str) -> bool:
        task = self._tasks.get(project_id)
        return task is not None and not task.done()

    async def start(self, project_id: str) -> DevProject:
        project = await self.store.get_project(project_id)
        if project is None:
            raise ValueError(f"Dev project '{project_id}' not found.")
        if self.is_running(project_id):
            raise ProjectAlreadyRunningError(f"Project '{project_id}' is already running.")
        validate_team(project.team())

        self._cancelled.discard(project_id)
        self._drop_retry(project_id)
        # Claim the project before the task's first await so a second start is rejected
        project.set_status(ProjectStatus.PLANNING)
        await self.store.save_project(project)

        if self.team_directory is not None:
            try:
                await self.team_directory.register(
                    project, project.provider or settings.STUDIO_PROVIDER, project.model
                )
            except Exception:  # the directory is a convenience; the team can work without it
                logger.exception("Could not register the team of %s as employees", project_id)

        orchestrator = self.orchestrator_factory(self.store, self.on_activity)
        task = asyncio.create_task(
            orchestrator.run_project(project_id, should_cancel=lambda: project_id in self._cancelled),
            name=f"studio-{project_id}",
        )
        self._tasks[project_id] = task
        task.add_done_callback(lambda finished: self._on_done(project_id, finished))
        return project

    def _on_done(self, project_id: str, task: "asyncio.Task[DevProject]") -> None:
        self._tasks.pop(project_id, None)
        self._cancelled.discard(project_id)
        if task.cancelled():
            return
        if task.exception() is not None:
            logger.error("Studio task for %s crashed", project_id, exc_info=task.exception())
            return
        if task.result().status == ProjectStatus.WAITING_FOR_QUOTA:
            self._schedule_retry(project_id)

    def _schedule_retry(self, project_id: str) -> None:
        async def retry() -> None:
            await asyncio.sleep(self.quota_retry_seconds)
            self._retries.pop(project_id, None)
            try:
                await self.start(project_id)
            except Exception:
                logger.exception("Could not resume %s after waiting for quota", project_id)

        self._drop_retry(project_id)
        self._retries[project_id] = asyncio.create_task(retry(), name=f"studio-retry-{project_id}")

    def _drop_retry(self, project_id: str) -> None:
        pending = self._retries.pop(project_id, None)
        if pending is not None and pending is not asyncio.current_task():
            pending.cancel()

    async def cancel(self, project_id: str) -> bool:
        """Stop a running project at its next step, or stop it waiting for quota."""
        if project_id in self._retries:
            self._drop_retry(project_id)
            project = await self.store.get_project(project_id)
            if project is not None:
                project.set_status(ProjectStatus.CANCELLED)
                await self.store.save_project(project)
            return True
        if not self.is_running(project_id):
            return False
        self._cancelled.add(project_id)
        return True

    async def wait(self, project_id: str) -> None:
        task = self._tasks.get(project_id)
        if task is not None:
            await asyncio.wait([task])

    async def shutdown(self) -> None:
        pending = [*self._tasks.values(), *self._retries.values()]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self._retries.clear()

    async def recover_interrupted(self, resume: bool | None = None) -> list[str]:
        """
        Called at startup. Nothing can be running yet, so projects recorded as active were cut
        off by the previous process: they are marked INTERRUPTED and, unless disabled, restarted.
        """
        recover = getattr(self.store, "mark_active_as_interrupted", None)
        project_ids: list[str] = await recover() if recover is not None else []
        if resume if resume is not None else settings.STUDIO_AUTO_RESUME:
            for project_id in project_ids:
                try:
                    await self.start(project_id)
                except Exception:
                    logger.exception("Could not resume studio project %s", project_id)
        return project_ids

    # ----------------------------------------------------------------- human
    async def ask(self, project_id: str, question: str, asked_by: str = "human") -> str:
        orchestrator = self.orchestrator_factory(self.store, self.on_activity)
        return await orchestrator.answer_question(project_id, question, asked_by)

    async def send_guidance(self, project_id: str, text: str, sent_by: str = "human") -> None:
        orchestrator = self.orchestrator_factory(self.store, self.on_activity)
        await orchestrator.add_guidance(project_id, text, sent_by)

    async def decide_ticket(
        self, project_id: str, ticket_id: str, approved: bool, feedback: str = ""
    ) -> bool:
        """Record a human decision on a ticket awaiting approval. False if it is not waiting."""
        return await self.store.set_ticket_approval(
            project_id, ticket_id, "APPROVED" if approved else "REJECTED", feedback
        )

    # ------------------------------------------------------------------ view
    async def team_view(self, project: DevProject) -> list[dict[str, Any]]:
        """Each team member with what they are doing right now, for the office view."""
        tickets = await self.store.list_tickets(project.id)
        events = await self.store.list_events(project.id, after=0, limit=10_000)
        last_activity: dict[str, str] = {}
        for event in events:
            if event.kind in ("tool_call", "status"):
                last_activity[event.actor_id] = event.summary

        active = project.status in ACTIVE_PROJECT_STATUSES and self.is_running(project.id)
        view = []
        for member in project.team():
            ticket = next(
                (t for t in tickets if t.assignee_id == member.id and t.status in _ACTIVE_TICKET_STATES),
                None,
            )
            if not active:
                state = "IDLE"
            elif ticket is not None:
                state = _ACTIVE_TICKET_STATES[ticket.status]
            elif member.role == TeamRole.MANAGER and project.status == ProjectStatus.PLANNING:
                state = "THINKING"
            else:
                state = "IDLE"
            view.append(
                {
                    "id": member.id,
                    "name": member.name,
                    "role": member.role.value,
                    "state": state,
                    "activity": last_activity.get(member.id, "") if state != "IDLE" else "",
                    "ticket_id": ticket.id if ticket else None,
                    "ticket_title": ticket.title if ticket else None,
                }
            )
        return view
