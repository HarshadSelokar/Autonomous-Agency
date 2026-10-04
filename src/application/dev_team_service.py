"""
Dev Team Orchestrator: runs a software project with a small team of agents.

    Manager    looks at the repository and breaks the goal into tickets
    Developers work tickets in parallel, each in its own git worktree
    QA         runs the project's test command (deterministic, not a model opinion)
    Reviewer   reads the diff and approves or sends the ticket back
    Human      optionally signs off each ticket before it is merged

Approved work is merged into the project's branch. Nothing is pushed: delivery to a
remote stays a human decision.
"""

import asyncio
import json
import logging
import re
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol

from src.application.agent_engine import AgentEngine, AgentTask
from src.application.agent_loop import AgentLoop, AgentLoopResult
from src.domain.dev_project import (
    IN_FLIGHT_TICKET_STATUSES,
    ActivityEvent,
    DevProject,
    DevTicket,
    ProjectStatus,
    TeamMember,
    TeamRole,
    TicketStatus,
)
from src.domain.exceptions import CancellationError, QuotaExhaustedError
from src.infrastructure.coding.agy_engine import AgyEngine
from src.infrastructure.coding.command_runner import CommandNotAllowedError, CommandRunner
from src.infrastructure.coding.loop_engine import LoopEngine
from src.infrastructure.coding.workspace import ProjectWorkspace, prepare_workspace
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

MAX_TICKETS = 12
HUMAN_ACTOR_ROLE = "HUMAN"
ActivityListener = Callable[[ActivityEvent], Awaitable[None]]
CancelCheck = Callable[[], bool] | None


class DevProjectStore(Protocol):
    async def save_project(self, project: DevProject) -> None: ...
    async def get_project(self, project_id: str) -> DevProject | None: ...
    async def list_projects(self, tenant_id: str | None = None) -> list[DevProject]: ...
    async def save_ticket(self, ticket: DevTicket) -> None: ...
    async def list_tickets(self, project_id: str) -> list[DevTicket]: ...
    async def add_event(self, event: ActivityEvent) -> ActivityEvent: ...
    async def list_events(
        self, project_id: str, after: int = 0, limit: int = 200
    ) -> list[ActivityEvent]: ...
    async def set_ticket_approval(
        self, project_id: str, ticket_id: str, approval: str, feedback: str
    ) -> bool: ...
    async def set_members(self, project_id: str, members: list[dict[str, str]]) -> None: ...
    async def delete_project(self, project_id: str) -> None: ...


class InMemoryDevProjectStore:
    """Process-local store, used by tests and scripts."""

    def __init__(self) -> None:
        self.projects: dict[str, DevProject] = {}
        self.tickets: dict[str, DevTicket] = {}
        self.events: list[ActivityEvent] = []

    async def save_project(self, project: DevProject) -> None:
        self.projects[project.id] = project

    async def get_project(self, project_id: str) -> DevProject | None:
        return self.projects.get(project_id)

    async def list_projects(self, tenant_id: str | None = None) -> list[DevProject]:
        return [p for p in self.projects.values() if tenant_id is None or p.tenant_id == tenant_id]

    async def save_ticket(self, ticket: DevTicket) -> None:
        self.tickets[ticket.id] = ticket

    async def list_tickets(self, project_id: str) -> list[DevTicket]:
        return sorted(
            (t for t in self.tickets.values() if t.project_id == project_id),
            key=lambda t: t.sequence,
        )

    async def add_event(self, event: ActivityEvent) -> ActivityEvent:
        event.sequence = 1 + sum(1 for e in self.events if e.project_id == event.project_id)
        self.events.append(event)
        return event

    async def list_events(
        self, project_id: str, after: int = 0, limit: int = 200
    ) -> list[ActivityEvent]:
        matching = [e for e in self.events if e.project_id == project_id and e.sequence > after]
        return matching[:limit]

    async def set_ticket_approval(
        self, project_id: str, ticket_id: str, approval: str, feedback: str
    ) -> bool:
        ticket = self.tickets.get(ticket_id)
        if ticket is None or ticket.project_id != project_id:
            return False
        if ticket.status != TicketStatus.AWAITING_APPROVAL:
            return False
        ticket.approval, ticket.approval_feedback = approval, feedback
        return True

    async def set_members(self, project_id: str, members: list[dict[str, str]]) -> None:
        self.projects[project_id].members = members

    async def delete_project(self, project_id: str) -> None:
        self.projects.pop(project_id, None)
        self.tickets = {k: t for k, t in self.tickets.items() if t.project_id != project_id}
        self.events = [e for e in self.events if e.project_id != project_id]


def extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of a model reply (tolerates code fences and prose)."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


MANAGER_PROMPT = """You are {name}, the engineering manager of a small autonomous software team.
Break the goal into tickets for your developers. A snapshot of the repository is included
below; read further files only if the snapshot is not enough.

Rules:
- Use as few tickets as the work honestly needs (between 1 and {max_tickets}). Each must be a
  concrete code change that can be reviewed on its own.
- Keep the tests for a behaviour in the same ticket as the behaviour. Never make "write the
  tests" a separate ticket.
- {developers} developer(s) work at the same time. List dependencies by ticket number only where
  one ticket really needs another's code; independent tickets should touch different files.
- If the project has no test command yet, propose one in "test_command" (a single program
  invocation such as "pytest -q" or "npm test"), or an empty string if none applies.

When you are ready, call the submit_plan tool. If you cannot call it, reply with
ONLY this JSON object and nothing else:
{{"summary": "one paragraph plan",
  "test_command": "pytest -q",
  "tickets": [{{"title": "...", "description": "...", "acceptance_criteria": "...", "depends_on": [1]}}]}}"""

DEVELOPER_PROMPT = """You are {name}, a software developer on a small autonomous team.
You work inside one project repository using your tools: read before you edit, keep changes
focused on the ticket, and run the tests or build to check your work.

Rules:
- Stay within the ticket's scope; do not refactor unrelated code.
- Do not commit: the team commits your work after QA and review.
- Commands run one at a time with no shell operators.

When the ticket is finished, reply with a short summary of what you changed and how you
checked it. That reply ends your turn."""

REVIEWER_PROMPT = """You are {name}, the code reviewer on a small autonomous software team.
You are given a ticket and the complete diff that claims to implement it. Decide from the
diff; read other files only when the diff alone cannot settle a question. Approve only if the
change is correct, meets the acceptance criteria, and does not break or remove unrelated
behaviour.

Give your verdict by calling the submit_review tool. If you cannot call it, reply with ONLY
this JSON object and nothing else:
{{"approved": true, "feedback": "what is good, or exactly what must change"}}"""

ASK_PROMPT = """You are {name}, the engineering manager of a small autonomous software team.
The person you work for is asking about the project. Answer briefly and concretely from the
project state below and the repository. You may only read; do not change anything."""

SUBMIT_PLAN_TOOL: dict[str, Any] = {
    "name": "submit_plan",
    "description": "Submit the final plan. Call this once, when you are ready.",
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "test_command": {"type": "string", "description": "Empty string if none applies."},
            "tickets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "acceptance_criteria": {"type": "string"},
                        "depends_on": {"type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["title", "description"],
                },
            },
        },
        "required": ["summary", "tickets"],
    },
}

SUBMIT_REVIEW_TOOL: dict[str, Any] = {
    "name": "submit_review",
    "description": "Submit your review verdict. Call this once.",
    "parameters": {
        "type": "object",
        "properties": {"approved": {"type": "boolean"}, "feedback": {"type": "string"}},
        "required": ["approved", "feedback"],
    },
}


class DevTeamOrchestrator:
    def __init__(
        self,
        store: DevProjectStore,
        agent_loop: AgentLoop | None = None,
        runner: CommandRunner | None = None,
        on_activity: ActivityListener | None = None,
        max_rework_rounds: int | None = None,
        workspaces_dir: str | None = None,
        engines: dict[str, AgentEngine] | None = None,
        approval_poll_seconds: float | None = None,
    ) -> None:
        self.store = store
        self.runner = runner or CommandRunner()
        self.engines: dict[str, AgentEngine] = {
            "loop": LoopEngine(agent_loop, self.runner),
            "agy": AgyEngine(),
            **(engines or {}),
        }
        self.on_activity = on_activity
        self.max_rework_rounds = (
            max_rework_rounds if max_rework_rounds is not None else settings.STUDIO_MAX_REWORK_ROUNDS
        )
        self.workspaces_dir = workspaces_dir
        self.approval_poll_seconds = (
            approval_poll_seconds
            if approval_poll_seconds is not None
            else settings.STUDIO_APPROVAL_POLL_SECONDS
        )

    async def _save(self, project: DevProject) -> None:
        """
        Save the run's view of the project. The team roster is owned by the user (members can
        be renamed while the team works), so it is refreshed from storage, never overwritten.
        """
        stored = await self.store.get_project(project.id)
        if stored is not None and stored is not project:
            project.members = stored.members
        await self.store.save_project(project)

    # ----------------------------------------------------------------- events
    async def _emit(
        self,
        project: DevProject,
        member: TeamMember,
        kind: str,
        summary: str,
        ticket: DevTicket | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        # Use the member's current name: they can be renamed while the team works
        current = next((m for m in project.team() if m.id == member.id), member)
        event = await self.store.add_event(
            ActivityEvent(
                project_id=project.id,
                actor_id=member.id,
                actor_name=current.name,
                actor_role=member.role.value,
                kind=kind,
                summary=summary,
                ticket_id=ticket.id if ticket else None,
                detail=detail or {},
            )
        )
        if self.on_activity is not None:
            try:
                await self.on_activity(event)
            except Exception:  # a broken listener must not stop the team
                logger.exception("Activity listener failed for project %s", project.id)

    def _loop_sink(
        self, project: DevProject, member: TeamMember, ticket: DevTicket | None
    ) -> Callable[[dict[str, Any]], Awaitable[None]]:
        async def sink(event: dict[str, Any]) -> None:
            if event["type"] == "tool_call":
                await self._emit(
                    project,
                    member,
                    "tool_call",
                    event["summary"],
                    ticket,
                    {"tool": event["tool"], "arguments": _compact(event["arguments"])},
                )
            elif event["type"] == "tool_result" and event["is_error"]:
                await self._emit(
                    project,
                    member,
                    "tool_result",
                    f"{event['summary']} failed",
                    ticket,
                    {"tool": event["tool"], "preview": event["preview"]},
                )

        return sink

    async def _guidance(self, project: DevProject) -> str:
        """Notes the human has sent to the team, newest last."""
        events = await self.store.list_events(project.id, after=0, limit=10_000)
        notes = [e.summary for e in events if e.kind == "human_message" and e.detail.get("guidance")]
        if not notes:
            return ""
        return "\n\nInstructions from the person you work for (follow them):\n" + "\n".join(
            f"- {note}" for note in notes
        )

    # ----------------------------------------------------------------- agents
    async def _run_agent(
        self,
        project: DevProject,
        member: TeamMember,
        system_prompt: str,
        user_prompt: str,
        workspace: ProjectWorkspace,
        read_only: bool,
        ticket: DevTicket | None,
        should_cancel: CancelCheck,
        final_tool: dict[str, Any] | None = None,
    ) -> AgentLoopResult:
        engine_name = project.engine or settings.STUDIO_ENGINE
        engine = self.engines.get(engine_name)
        if engine is None:
            raise ValueError(
                f"Unknown studio engine '{engine_name}'. Available: {', '.join(sorted(self.engines))}."
            )
        result = await engine.run(
            AgentTask(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                workspace_root=workspace.root,
                read_only=read_only,
                final_tool=final_tool,
            ),
            provider=project.provider or settings.STUDIO_PROVIDER,
            model=self._model_for(project, member, engine_name),
            on_event=self._loop_sink(project, member, ticket),
            should_cancel=should_cancel,
        )
        project.add_usage(result.usage)
        return result

    @staticmethod
    def _model_for(project: DevProject, member: TeamMember, engine_name: str) -> str:
        """A project-level model applies to every role; otherwise agy uses per-role defaults."""
        if project.model:
            return project.model
        if engine_name == "agy":
            return {
                TeamRole.MANAGER: settings.AGY_MODEL_MANAGER,
                TeamRole.DEVELOPER: settings.AGY_MODEL_DEVELOPER,
                TeamRole.REVIEWER: settings.AGY_MODEL_REVIEWER,
            }.get(member.role, settings.AGY_MODEL_DEVELOPER)
        return settings.STUDIO_MODEL

    async def _ask_for_json(
        self,
        project: DevProject,
        member: TeamMember,
        system_prompt: str,
        user_prompt: str,
        workspace: ProjectWorkspace,
        ticket: DevTicket | None,
        should_cancel: CancelCheck,
        final_tool: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Run an agent that must end with a structured answer: the final tool's arguments,
        or a JSON object in plain text. One repair attempt is allowed.
        """
        result = await self._run_agent(
            project, member, system_prompt, user_prompt, workspace, True, ticket, should_cancel, final_tool
        )
        parsed = result.final_payload or extract_json(result.final_text)
        if parsed is not None:
            return parsed
        repair_prompt = (
            f"{user_prompt}\n\nYour previous reply could not be parsed as JSON:\n"
            f"{result.final_text[:2000]}\n\n"
            f"Call {final_tool['name']} or reply with ONLY the JSON object."
        )
        result = await self._run_agent(
            project, member, system_prompt, repair_prompt, workspace, True, ticket, should_cancel, final_tool
        )
        return result.final_payload or extract_json(result.final_text)

    async def answer_question(self, project_id: str, question: str, asked_by: str = "human") -> str:
        """The manager answers a question about the project. Read-only; safe while it runs."""
        project = await self.store.get_project(project_id)
        if project is None:
            raise ValueError(f"Dev project '{project_id}' not found.")
        manager = project.member(TeamRole.MANAGER)
        await self._emit_human(project, asked_by, question, guidance=False)

        tickets = await self.store.list_tickets(project.id)
        board = "\n".join(
            f"- [{t.status.value}] {t.title}" + (f" (feedback: {t.feedback[:200]})" if t.feedback else "")
            for t in tickets
        )
        state = (
            f"Goal: {project.goal}\nStatus: {project.status.value}\nPlan: {project.summary}\n"
            f"Tickets:\n{board or '(none yet)'}\n\nQuestion: {question}"
        )
        if project.workspace_path and Path(project.workspace_path).is_dir():
            result = await self._run_agent(
                project,
                manager,
                ASK_PROMPT.format(name=manager.name),
                state,
                ProjectWorkspace(Path(project.workspace_path)),
                True,
                None,
                None,
            )
            answer = result.final_text.strip() or "I could not produce an answer."
        else:
            answer = "The project has not started yet, so there is nothing to report."
        await self._emit(project, manager, "message", answer[:500], None, {"answer": answer})
        return answer

    async def _emit_human(self, project: DevProject, actor: str, text: str, guidance: bool) -> None:
        human = TeamMember(id=actor, name="You", role=TeamRole.MANAGER)
        event = await self.store.add_event(
            ActivityEvent(
                project_id=project.id,
                actor_id=actor,
                actor_name=human.name,
                actor_role=HUMAN_ACTOR_ROLE,
                kind="human_message",
                summary=text[:500],
                detail={"guidance": guidance, "text": text},
            )
        )
        if self.on_activity is not None:
            try:
                await self.on_activity(event)
            except Exception:
                logger.exception("Activity listener failed for project %s", project.id)

    async def add_guidance(self, project_id: str, text: str, sent_by: str = "human") -> None:
        """An instruction from the human that every later brief will carry."""
        project = await self.store.get_project(project_id)
        if project is None:
            raise ValueError(f"Dev project '{project_id}' not found.")
        await self._emit_human(project, sent_by, text, guidance=True)

    # ------------------------------------------------------------------- run
    async def run_project(self, project_id: str, should_cancel: CancelCheck = None) -> DevProject:
        project = await self.store.get_project(project_id)
        if project is None:
            raise ValueError(f"Dev project '{project_id}' not found.")
        manager = project.member(TeamRole.MANAGER)

        try:
            workspace = await self._open_workspace(project)
            tickets = await self.store.list_tickets(project.id)
            if not tickets:
                tickets = await self._plan(project, workspace, should_cancel)
            else:
                await self._reset_interrupted(project, workspace, tickets)

            project.set_status(ProjectStatus.RUNNING)
            await self._save(project)

            await self._work_all(project, workspace, tickets, should_cancel)

            done = sum(1 for t in tickets if t.status == TicketStatus.DONE)
            blocked = len(tickets) - done
            project.summary = (
                f"{done} of {len(tickets)} tickets completed on branch '{project.branch}'."
                + (f" {blocked} need attention." if blocked else "")
            )
            project.set_status(
                ProjectStatus.COMPLETED if blocked == 0 else ProjectStatus.NEEDS_ATTENTION
            )
            await self._save(project)
            await self._emit(project, manager, "project", project.summary)
        except CancellationError:
            project.set_status(ProjectStatus.CANCELLED)
            await self._save(project)
            await self._emit(project, manager, "project", "Project cancelled.")
        except QuotaExhaustedError as exc:
            project.set_status(ProjectStatus.WAITING_FOR_QUOTA, failure_reason=str(exc)[:1000])
            await self._save(project)
            await self._emit(project, manager, "project", "Out of model quota; waiting to resume.")
        except Exception as exc:
            logger.exception("Dev project %s failed", project.id)
            project.set_status(ProjectStatus.FAILED, failure_reason=f"{type(exc).__name__}: {exc}")
            await self._save(project)
            await self._emit(project, manager, "project", f"Project failed: {exc}")
        return project

    async def _work_all(
        self,
        project: DevProject,
        workspace: ProjectWorkspace,
        tickets: list[DevTicket],
        should_cancel: CancelCheck,
    ) -> None:
        """Hand ready tickets to free developers until nothing more can be started."""
        manager = project.member(TeamRole.MANAGER)
        by_id = {t.id: t for t in tickets}
        free = list(project.developers())
        # Merging into the project branch is the one step developers must take turns at
        merge_lock = asyncio.Lock()
        running: dict[asyncio.Task[None], TeamMember] = {}

        try:
            while True:
                if should_cancel is not None and should_cancel():
                    raise CancellationError("Project cancelled.")

                for ticket in tickets:
                    if ticket.status != TicketStatus.TODO:
                        continue
                    dependencies = [by_id[d] for d in ticket.depends_on if d in by_id]
                    blocked_by = [d.title for d in dependencies if d.status == TicketStatus.BLOCKED]
                    if blocked_by:
                        ticket.feedback = f"Blocked by unfinished ticket(s): {', '.join(blocked_by)}"
                        await self._move(project, manager, ticket, TicketStatus.BLOCKED, None)
                        continue
                    if any(d.status != TicketStatus.DONE for d in dependencies) or not free:
                        continue
                    developer = free.pop(0)
                    # Claimed here, before the task first runs, so it is not started twice
                    ticket.move_to(TicketStatus.IN_PROGRESS, developer.id)
                    task = asyncio.create_task(
                        self._work_ticket(project, workspace, ticket, developer, merge_lock, should_cancel)
                    )
                    running[task] = developer

                if not running:
                    return
                finished, _ = await asyncio.wait(
                    running.keys(), timeout=1.0, return_when=asyncio.FIRST_COMPLETED
                )
                for task in finished:
                    free.append(running.pop(task))
                    task.result()  # re-raise whatever stopped the ticket
                    await self._save(project)
        finally:
            for task in running:
                task.cancel()
            if running:
                await asyncio.gather(*running.keys(), return_exceptions=True)

    async def _open_workspace(self, project: DevProject) -> ProjectWorkspace:
        workspace, branch, base_commit = await prepare_workspace(
            project.id,
            repo_url=project.repo_url,
            local_path=project.local_path,
            base_dir=self.workspaces_dir,
        )
        project.workspace_path = str(workspace.root)
        project.branch = branch
        if not project.base_commit:
            project.base_commit = base_commit
        await self._save(project)
        return workspace

    @staticmethod
    def _worktree_path(workspace: ProjectWorkspace, ticket: DevTicket) -> Path:
        return workspace.root.parent / f"{workspace.root.name}.worktrees" / ticket.id

    @staticmethod
    def _ticket_branch(project: DevProject, ticket: DevTicket) -> str:
        # A sibling of the project branch: git cannot nest a branch under an existing one
        return f"agency-ticket/{project.id}/{ticket.id}"

    async def _reset_interrupted(
        self, project: DevProject, workspace: ProjectWorkspace, tickets: list[DevTicket]
    ) -> None:
        """On restart, half-finished tickets go back to TODO and their unmerged work goes."""
        await workspace.discard_pending()
        for ticket in tickets:
            if ticket.status not in IN_FLIGHT_TICKET_STATUSES:
                continue
            await workspace.remove_worktree(
                self._worktree_path(workspace, ticket), self._ticket_branch(project, ticket)
            )
            ticket.approval = ""
            ticket.move_to(TicketStatus.TODO)
            await self.store.save_ticket(ticket)

    async def _move(
        self,
        project: DevProject,
        member: TeamMember,
        ticket: DevTicket,
        status: TicketStatus,
        assignee_id: str | None,
    ) -> None:
        ticket.move_to(status, assignee_id)
        await self.store.save_ticket(ticket)
        await self._emit(
            project,
            member,
            "ticket",
            f"'{ticket.title}' moved to {status.value}",
            ticket,
            {"status": status.value},
        )

    # ------------------------------------------------------------------ plan
    async def _plan(
        self,
        project: DevProject,
        workspace: ProjectWorkspace,
        should_cancel: CancelCheck,
    ) -> list[DevTicket]:
        manager = project.member(TeamRole.MANAGER)
        project.set_status(ProjectStatus.PLANNING)
        await self._save(project)
        await self._emit(project, manager, "status", "planning the work")

        plan = await self._ask_for_json(
            project,
            manager,
            MANAGER_PROMPT.format(
                name=manager.name, max_tickets=MAX_TICKETS, developers=len(project.developers())
            ),
            (
                f"Goal:\n{project.goal}\n\nCurrent test command: {project.test_command or 'none'}"
                f"{await self._guidance(project)}\n\nRepository snapshot:\n{workspace.snapshot()}"
            ),
            workspace,
            None,
            should_cancel,
            SUBMIT_PLAN_TOOL,
        )
        raw_tickets = (plan or {}).get("tickets")
        if not isinstance(raw_tickets, list) or not raw_tickets:
            raise ValueError("The manager did not produce a usable plan (no tickets).")

        if not project.test_command:
            proposed = (plan or {}).get("test_command")
            if isinstance(proposed, str) and proposed.strip():
                try:
                    self.runner.validate(proposed, workspace.root)
                    project.test_command = proposed.strip()
                except CommandNotAllowedError as exc:
                    await self._emit(
                        project, manager, "status", f"proposed test command rejected: {exc}"
                    )

        tickets: list[DevTicket] = []
        dependencies: dict[str, list[Any]] = {}
        for index, raw in enumerate(raw_tickets[:MAX_TICKETS], start=1):
            if not isinstance(raw, dict) or not str(raw.get("title", "")).strip():
                continue
            tickets.append(
                DevTicket(
                    id=f"tkt-{uuid.uuid4().hex[:10]}",
                    project_id=project.id,
                    sequence=index,
                    title=str(raw["title"]).strip()[:200],
                    description=str(raw.get("description", "")),
                    acceptance_criteria=str(raw.get("acceptance_criteria", "")),
                )
            )
            raw_deps = raw.get("depends_on")
            dependencies[tickets[-1].id] = raw_deps if isinstance(raw_deps, list) else []
        if not tickets:
            raise ValueError("The manager's plan contained no valid tickets.")

        by_sequence = {t.sequence: t for t in tickets}
        for ticket in tickets:
            for dep in dependencies[ticket.id]:
                # Only backward references are honoured, which keeps the plan acyclic
                if isinstance(dep, int) and dep in by_sequence and dep < ticket.sequence:
                    ticket.depends_on.append(by_sequence[dep].id)

        for ticket in tickets:
            await self.store.save_ticket(ticket)
        project.summary = str((plan or {}).get("summary", ""))[:2000]
        await self._save(project)
        await self._emit(
            project,
            manager,
            "status",
            f"created {len(tickets)} tickets",
            None,
            {"tickets": [t.title for t in tickets]},
        )
        return tickets

    # ---------------------------------------------------------------- ticket
    async def _work_ticket(
        self,
        project: DevProject,
        workspace: ProjectWorkspace,
        ticket: DevTicket,
        developer: TeamMember,
        merge_lock: asyncio.Lock,
        should_cancel: CancelCheck,
    ) -> None:
        qa = project.member(TeamRole.QA)
        reviewer = project.member(TeamRole.REVIEWER)
        branch = self._ticket_branch(project, ticket)
        worktree_path = self._worktree_path(workspace, ticket)
        async with merge_lock:
            worktree = await workspace.add_worktree(worktree_path, branch, project.branch)
        feedback = ""

        try:
            for attempt in range(1, self.max_rework_rounds + 2):
                ticket.attempts = attempt
                await self._move(project, developer, ticket, TicketStatus.IN_PROGRESS, developer.id)

                dev_result = await self._run_agent(
                    project,
                    developer,
                    DEVELOPER_PROMPT.format(name=developer.name),
                    await self._developer_brief(project, worktree, ticket, feedback),
                    worktree,
                    False,
                    ticket,
                    should_cancel,
                )
                ticket.result_summary = dev_result.final_text[:2000]

                if dev_result.violations:
                    # The engine could not stop this, so the attempt is thrown away
                    await worktree.discard_pending()
                    feedback = (
                        "Your attempt was discarded because you " + "; ".join(dev_result.violations)
                        + ". Keep every change inside the project directory."
                    )
                    ticket.feedback = feedback
                    await self._emit(
                        project, developer, "violation", "wrote outside the project; attempt discarded",
                        ticket, {"violations": dev_result.violations},
                    )
                    continue

                diff = await worktree.diff_from_fork(project.branch)
                no_changes = not diff.strip()
                if no_changes:
                    await self._emit(project, developer, "status", "made no changes", ticket)
                    if not dev_result.completed:
                        feedback = "You ran out of steps before changing anything. Work more directly."
                        ticket.feedback = feedback
                        continue
                    # The developer says nothing needed changing (an earlier ticket may have
                    # covered it). That claim still goes through QA and review below.

                failure = await self._run_tests(project, qa, ticket, worktree)
                if failure:
                    feedback = ticket.feedback = failure
                    continue

                await self._move(project, reviewer, ticket, TicketStatus.IN_REVIEW, reviewer.id)
                if no_changes:
                    evidence = (
                        "The developer changed no files and reports the ticket is already satisfied "
                        f"by the existing code:\n{dev_result.final_text[:2000]}\n\n"
                        "Check the code yourself. Approve only if every acceptance criterion is "
                        "already met; otherwise say what is missing."
                    )
                else:
                    # Tests may have written files (caches, snapshots); review what will be merged
                    diff = await worktree.diff_from_fork(project.branch)
                    evidence = f"Diff:\n{diff}"
                verdict = await self._ask_for_json(
                    project,
                    reviewer,
                    REVIEWER_PROMPT.format(name=reviewer.name),
                    (
                        f"Ticket: {ticket.title}\n\n{ticket.description}\n\n"
                        f"Acceptance criteria:\n{ticket.acceptance_criteria}"
                        f"{await self._guidance(project)}\n\n{evidence}"
                    ),
                    worktree,
                    ticket,
                    should_cancel,
                    SUBMIT_REVIEW_TOOL,
                )
                approved = bool(verdict and verdict.get("approved") is True)
                review_feedback = (
                    str((verdict or {}).get("feedback", "")) or "Review reply was unreadable."
                )
                if not approved:
                    feedback = f"Code review requested changes:\n{review_feedback}"
                    ticket.feedback = feedback
                    await self._emit(
                        project, reviewer, "status", "requested changes", ticket,
                        {"feedback": review_feedback[:1500]},
                    )
                    continue
                await self._emit(project, reviewer, "status", "approved the change", ticket)

                if project.require_approval:
                    rejection = await self._await_human(project, ticket, diff, should_cancel)
                    if rejection is not None:
                        feedback = ticket.feedback = f"The person you work for rejected this:\n{rejection}"
                        continue

                conflict = await self._merge(project, workspace, worktree, ticket, branch, qa, merge_lock)
                if conflict:
                    feedback = ticket.feedback = conflict
                    continue

                ticket.feedback = review_feedback
                await self._move(project, reviewer, ticket, TicketStatus.DONE, None)
                return

            await self._move(project, project.member(TeamRole.MANAGER), ticket, TicketStatus.BLOCKED, None)
        finally:
            async with merge_lock:
                await workspace.remove_worktree(worktree_path, branch)

    async def _run_tests(
        self, project: DevProject, qa: TeamMember, ticket: DevTicket, worktree: ProjectWorkspace
    ) -> str:
        """Run the project's test command in the ticket's worktree. Returns '' or the failure."""
        if not project.test_command:
            return ""
        await self._move(project, qa, ticket, TicketStatus.TESTING, qa.id)
        await self._emit(project, qa, "tool_call", "running tests", ticket)
        test = await self.runner.run(project.test_command, worktree.root)
        if test.ok:
            await self._emit(project, qa, "status", "tests passed", ticket)
            return ""
        await self._emit(
            project, qa, "status", "tests failed, sending back", ticket, {"output": test.output[-1500:]}
        )
        return f"`{project.test_command}` failed:\n{test.output[-4000:]}"

    async def _await_human(
        self, project: DevProject, ticket: DevTicket, diff: str, should_cancel: CancelCheck
    ) -> str | None:
        """Wait for a human to approve or reject the ticket. Returns the rejection text, or None."""
        manager = project.member(TeamRole.MANAGER)
        ticket.approval = ""
        ticket.approval_feedback = ""
        await self._move(project, manager, ticket, TicketStatus.AWAITING_APPROVAL, None)
        await self._emit(
            project, manager, "status", "waiting for your approval", ticket, {"diff": diff[:20_000]}
        )
        while True:
            if should_cancel is not None and should_cancel():
                raise CancellationError("Project cancelled.")
            current = next(
                (t for t in await self.store.list_tickets(project.id) if t.id == ticket.id), None
            )
            decision = current.approval if current else ""
            if decision == "APPROVED":
                ticket.approval = "APPROVED"
                return None
            if decision == "REJECTED":
                ticket.approval = "REJECTED"
                ticket.approval_feedback = current.approval_feedback if current else ""
                return ticket.approval_feedback or "No reason given."
            await asyncio.sleep(self.approval_poll_seconds)

    async def _merge(
        self,
        project: DevProject,
        workspace: ProjectWorkspace,
        worktree: ProjectWorkspace,
        ticket: DevTicket,
        branch: str,
        qa: TeamMember,
        merge_lock: asyncio.Lock,
    ) -> str:
        """Commit the ticket and bring it onto the project branch. Returns '' or the problem."""
        diff = await worktree.diff_from_fork(project.branch)
        await worktree.commit(f"{ticket.title}\n\nTicket: {ticket.id}")
        async with merge_lock:
            ahead = (await worktree.git("rev-list", "--count", f"{project.branch}..{branch}")).output.strip()
            if ahead in ("", "0"):
                ticket.commit_sha = ""
                return ""
            behind = (await worktree.git("rev-list", "--count", f"{branch}..{project.branch}")).output.strip()
            if behind not in ("", "0"):
                # Other tickets were merged while this one was in progress
                if not await worktree.rebase_onto(project.branch):
                    await worktree.reset_to(project.branch)
                    await self._emit(
                        project, qa, "status", "conflicts with newer work, sending back", ticket
                    )
                    return (
                        "Your change conflicted with work that was merged while you were working, "
                        "so it was dropped. Re-apply it on top of the current code. This was your "
                        f"diff:\n{diff[:6000]}"
                    )
                failure = await self._run_tests(project, qa, ticket, worktree)
                if failure:
                    return f"After combining with newer work, {failure}"
            await workspace.merge_fast_forward(branch)
            ticket.commit_sha = await worktree.head()
        return ""

    async def _developer_brief(
        self, project: DevProject, worktree: ProjectWorkspace, ticket: DevTicket, feedback: str
    ) -> str:
        brief = (
            f"Project goal:\n{project.goal}\n\n"
            f"Your ticket: {ticket.title}\n\n{ticket.description}\n\n"
            f"Acceptance criteria:\n{ticket.acceptance_criteria or 'Not specified.'}\n\n"
            f"Test command: {project.test_command or 'none configured'}"
            f"{await self._guidance(project)}"
        )
        if feedback:
            brief += (
                "\n\nYour previous attempt was sent back. Your earlier edits are still in the "
                f"working tree unless told otherwise. Fix this:\n{feedback}"
            )
        brief += (
            "\n\nRepository snapshot (current; no need to re-read files shown here):\n"
            f"{worktree.snapshot()}"
        )
        return brief


def _compact(arguments: dict[str, Any]) -> dict[str, Any]:
    """Keep event payloads small: file contents do not belong in the activity feed."""
    return {
        key: (value if len(str(value)) <= 200 else f"{str(value)[:200]}...")
        for key, value in arguments.items()
    }
