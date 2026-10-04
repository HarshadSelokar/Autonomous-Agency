"""
FastAPI routes for the Software Studio: hand a goal to an autonomous dev team and watch it work.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from src.api.auth import Principal, ensure_tenant_access, get_principal
from src.application.studio_service import ProjectAlreadyRunningError, StudioService
from src.domain.dev_project import (
    ActivityEvent,
    DevProject,
    DevTicket,
    TeamRole,
    TeamValidationError,
    TicketStatus,
)
from src.domain.events import OfficeStateUpdatedEvent
from src.infrastructure.coding.workspace import ProjectWorkspace
from src.infrastructure.config import settings
from src.infrastructure.database import AsyncSessionLocal
from src.infrastructure.repositories.dev_project_repository import SQLAlchemyDevProjectStore
from src.infrastructure.repositories.studio_team_directory import StudioTeamDirectory

router = APIRouter(prefix="/studio", tags=["Software Studio"])

_VISUAL_STATE_BY_KIND = {"tool_call": "WORKING", "tool_result": "BLOCKED", "status": "WORKING"}
_studio: StudioService | None = None


async def _broadcast_to_office(event: ActivityEvent) -> None:
    """Relay team activity to Pixel Office WebSocket clients."""
    from src.api.routes.office import global_broadcaster

    await global_broadcaster.broadcast_event(
        OfficeStateUpdatedEvent(
            employee_id=event.actor_id,
            visual_state=_VISUAL_STATE_BY_KIND.get(event.kind, "IDLE"),
            activity_summary=event.summary,
            task_id=event.ticket_id,
            project_id=event.project_id,
        )
    )


def get_studio() -> StudioService:
    global _studio
    if _studio is None:
        _studio = StudioService(
            store=SQLAlchemyDevProjectStore(AsyncSessionLocal),
            on_activity=_broadcast_to_office,
            team_directory=StudioTeamDirectory(AsyncSessionLocal),
        )
    return _studio


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    goal: str = Field(..., min_length=10, max_length=20_000)
    repo_url: str | None = Field(default=None, description="https:// git URL to clone")
    local_path: str | None = Field(
        default=None, description="Path to a git repository on the server to clone (admins only)"
    )
    test_command: str | None = Field(default=None, max_length=512)
    engine: str = Field(default="", pattern="^(loop|agy|)$", description="loop, agy, or empty for the default")
    provider: str = ""
    model: str = ""
    developers: int | None = Field(default=None, ge=1, le=6, description="Developers working in parallel")
    require_approval: bool = Field(
        default=False, description="A human must approve each ticket before it is merged"
    )
    auto_start: bool = True


class MemberCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    role: TeamRole


class MemberRenameRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class DecisionRequest(BaseModel):
    feedback: str = Field(default="", max_length=4000)


class TicketResponse(BaseModel):
    id: str
    sequence: int
    title: str
    description: str
    acceptance_criteria: str
    status: str
    depends_on: list[str]
    assignee_id: str | None
    attempts: int
    feedback: str
    commit_sha: str | None
    result_summary: str
    approval: str
    approval_feedback: str
    updated_at: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    goal: str
    status: str
    is_running: bool
    repo_url: str | None
    branch: str
    base_commit: str
    workspace_path: str
    test_command: str | None
    engine: str
    provider: str
    model: str
    require_approval: bool
    summary: str
    failure_reason: str | None
    usage: dict[str, int]
    created_at: str
    updated_at: str


class ProjectDetailResponse(ProjectResponse):
    team: list[dict[str, Any]]
    tickets: list[TicketResponse]


class EventResponse(BaseModel):
    sequence: int
    kind: str
    summary: str
    actor_id: str
    actor_name: str
    actor_role: str
    ticket_id: str | None
    detail: dict[str, Any]
    created_at: str


def _ticket_response(ticket: DevTicket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        sequence=ticket.sequence,
        title=ticket.title,
        description=ticket.description,
        acceptance_criteria=ticket.acceptance_criteria,
        status=ticket.status.value,
        depends_on=ticket.depends_on,
        assignee_id=ticket.assignee_id,
        attempts=ticket.attempts,
        feedback=ticket.feedback,
        commit_sha=ticket.commit_sha,
        result_summary=ticket.result_summary,
        approval=ticket.approval,
        approval_feedback=ticket.approval_feedback,
        updated_at=ticket.updated_at.isoformat(),
    )


def _project_fields(project: DevProject, studio: StudioService) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "goal": project.goal,
        "status": project.status.value,
        "is_running": studio.is_running(project.id),
        "repo_url": project.repo_url,
        "branch": project.branch,
        "base_commit": project.base_commit,
        "workspace_path": project.workspace_path,
        "test_command": project.test_command,
        "engine": project.engine or settings.STUDIO_ENGINE,
        "provider": project.provider or settings.STUDIO_PROVIDER,
        "model": project.model or settings.STUDIO_MODEL,
        "require_approval": project.require_approval,
        "summary": project.summary,
        "failure_reason": project.failure_reason,
        "usage": project.usage,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


async def _load(
    project_id: str, studio: StudioService, principal: Principal | None
) -> DevProject:
    project = await studio.store.get_project(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project '{project_id}' not found.")
    ensure_tenant_access(principal, project.tenant_id)
    return project


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    request: Request,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> ProjectResponse:
    if payload.repo_url and payload.local_path:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Send repo_url or local_path, not both.")
    if payload.repo_url and not payload.repo_url.startswith("https://"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "repo_url must be an https:// URL.")
    if payload.local_path:
        # Cloning a server path reads the server's disk, so it is not open to every tenant user
        if settings.AUTH_REQUIRED and not (principal and principal.is_platform_admin):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "local_path requires a platform administrator.")
        if not (Path(payload.local_path) / ".git").exists():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "local_path is not a git repository.")

    project = await studio.create_project(
        name=payload.name,
        goal=payload.goal,
        tenant_id=getattr(request.state, "tenant_id", None),
        repo_url=payload.repo_url,
        local_path=payload.local_path,
        test_command=payload.test_command,
        engine=payload.engine,
        provider=payload.provider,
        model=payload.model,
        developers=payload.developers,
        require_approval=payload.require_approval,
        created_by=principal.user_id if principal else None,
    )
    if payload.auto_start:
        project = await studio.start(project.id)
    return ProjectResponse(**_project_fields(project, studio))


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    request: Request,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> list[ProjectResponse]:
    tenant_id = getattr(request.state, "tenant_id", None)
    if principal is not None and not principal.is_platform_admin:
        tenant_id = principal.tenant_id
    projects = await studio.store.list_projects(tenant_id=tenant_id)
    return [ProjectResponse(**_project_fields(p, studio)) for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> ProjectDetailResponse:
    project = await _load(project_id, studio, principal)
    tickets = await studio.store.list_tickets(project.id)
    return ProjectDetailResponse(
        **_project_fields(project, studio),
        team=await studio.team_view(project),
        tickets=[_ticket_response(t) for t in tickets],
    )


@router.get("/projects/{project_id}/board")
async def get_board(
    project_id: str,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, list[TicketResponse]]:
    """Tickets grouped into kanban columns."""
    project = await _load(project_id, studio, principal)
    tickets = await studio.store.list_tickets(project.id)
    board: dict[str, list[TicketResponse]] = {s.value: [] for s in TicketStatus}
    for ticket in tickets:
        board[ticket.status.value].append(_ticket_response(ticket))
    return board


@router.get("/projects/{project_id}/events", response_model=list[EventResponse])
async def list_events(
    project_id: str,
    after: int = Query(0, ge=0, description="Return events with a sequence greater than this"),
    limit: int = Query(200, ge=1, le=1000),
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> list[EventResponse]:
    project = await _load(project_id, studio, principal)
    events = await studio.store.list_events(project.id, after=after, limit=limit)
    return [
        EventResponse(
            sequence=e.sequence,
            kind=e.kind,
            summary=e.summary,
            actor_id=e.actor_id,
            actor_name=e.actor_name,
            actor_role=e.actor_role,
            ticket_id=e.ticket_id,
            detail=e.detail,
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]


@router.get("/projects/{project_id}/diff")
async def get_diff(
    project_id: str,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, Any]:
    """Everything the team has committed so far, relative to where the project started."""
    project = await _load(project_id, studio, principal)
    if not project.workspace_path or not Path(project.workspace_path).is_dir():
        return {"branch": project.branch, "commits": [], "diff": ""}
    workspace = ProjectWorkspace(Path(project.workspace_path))
    return {
        "branch": project.branch,
        "commits": await workspace.log_since(project.base_commit),
        "diff": await workspace.diff_since(project.base_commit),
    }


@router.post("/projects/{project_id}/start", response_model=ProjectResponse)
async def start_project(
    project_id: str,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> ProjectResponse:
    """Start a project, or restart one that was interrupted, cancelled or failed."""
    await _load(project_id, studio, principal)
    try:
        project = await studio.start(project_id)
    except ProjectAlreadyRunningError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return ProjectResponse(**_project_fields(project, studio))


@router.post("/projects/{project_id}/cancel")
async def cancel_project(
    project_id: str,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, Any]:
    await _load(project_id, studio, principal)
    requested = await studio.cancel(project_id)
    return {
        "project_id": project_id,
        "cancel_requested": requested,
        "detail": "The team stops at its next step." if requested else "Project is not running.",
    }


# ------------------------------------------------------------------------ team
def _team_response(project: DevProject) -> list[dict[str, str]]:
    return [member.to_dict() for member in project.team()]


async def _change_team(change: Any) -> list[dict[str, str]]:
    try:
        return _team_response(await change)
    except ProjectAlreadyRunningError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except TeamValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/projects/{project_id}/team", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    project_id: str,
    payload: MemberCreateRequest,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> list[dict[str, str]]:
    """Add an agent to the team (only while the project is not running)."""
    await _load(project_id, studio, principal)
    return await _change_team(studio.add_member(project_id, payload.name, payload.role))


@router.patch("/projects/{project_id}/team/{member_id}")
async def rename_team_member(
    project_id: str,
    member_id: str,
    payload: MemberRenameRequest,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> list[dict[str, str]]:
    await _load(project_id, studio, principal)
    return await _change_team(studio.rename_member(project_id, member_id, payload.name))


@router.delete("/projects/{project_id}/team/{member_id}")
async def remove_team_member(
    project_id: str,
    member_id: str,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> list[dict[str, str]]:
    await _load(project_id, studio, principal)
    return await _change_team(studio.remove_member(project_id, member_id))


# ----------------------------------------------------------------------- human
@router.post("/projects/{project_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_guidance(
    project_id: str,
    payload: MessageRequest,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, str]:
    """Give the team an instruction. Every brief written from now on carries it."""
    await _load(project_id, studio, principal)
    await studio.send_guidance(project_id, payload.text, principal.user_id if principal else "human")
    return {"status": "DELIVERED", "detail": "The team will follow this from their next step."}


@router.post("/projects/{project_id}/ask")
async def ask_manager(
    project_id: str,
    payload: MessageRequest,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, str]:
    """Ask the manager about the project. The manager reads the code and the board; nothing changes."""
    await _load(project_id, studio, principal)
    answer = await studio.ask(project_id, payload.text, principal.user_id if principal else "human")
    return {"answer": answer}


async def _decide(
    project_id: str, ticket_id: str, approved: bool, feedback: str, studio: StudioService
) -> dict[str, Any]:
    if not await studio.decide_ticket(project_id, ticket_id, approved, feedback):
        raise HTTPException(status.HTTP_409_CONFLICT, "This ticket is not awaiting approval.")
    return {"ticket_id": ticket_id, "decision": "APPROVED" if approved else "REJECTED"}


@router.post("/projects/{project_id}/tickets/{ticket_id}/approve")
async def approve_ticket(
    project_id: str,
    ticket_id: str,
    payload: DecisionRequest | None = None,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, Any]:
    await _load(project_id, studio, principal)
    return await _decide(project_id, ticket_id, True, payload.feedback if payload else "", studio)


@router.post("/projects/{project_id}/tickets/{ticket_id}/reject")
async def reject_ticket(
    project_id: str,
    ticket_id: str,
    payload: DecisionRequest,
    studio: StudioService = Depends(get_studio),
    principal: Principal | None = Depends(get_principal),
) -> dict[str, Any]:
    """Send the ticket back to its developer with your reason."""
    await _load(project_id, studio, principal)
    return await _decide(project_id, ticket_id, False, payload.feedback, studio)
