"""
SQLAlchemy store for the Software Studio.

A dev project runs for minutes to hours in a background task, so each operation opens its
own short session instead of holding one for the whole run.
"""

import asyncio
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.dev_project import (
    ACTIVE_PROJECT_STATUSES,
    ActivityEvent,
    DevProject,
    DevTicket,
    ProjectStatus,
    TicketStatus,
)
from src.infrastructure.models.dev_project_model import (
    DevActivityEventModel,
    DevProjectModel,
    DevTicketModel,
)

_PROJECT_FIELDS = (
    "id", "tenant_id", "name", "goal", "repo_url", "local_path", "workspace_path", "branch",
    "base_commit", "test_command", "engine", "provider", "model", "require_approval", "summary",
    "failure_reason",
    "created_by", "created_at", "updated_at",
)
_TICKET_FIELDS = (
    "id", "project_id", "sequence", "title", "description", "acceptance_criteria",
    "assignee_id", "attempts", "feedback", "commit_sha", "result_summary", "approval",
    "approval_feedback",
    "created_at", "updated_at",
)


def _project_to_domain(model: DevProjectModel) -> DevProject:
    values = {name: getattr(model, name) for name in _PROJECT_FIELDS}
    return DevProject(
        **values,
        status=ProjectStatus(model.status),
        usage=dict(model.usage or {}),
        members=list(model.members or []),
    )


def _ticket_to_domain(model: DevTicketModel) -> DevTicket:
    values = {name: getattr(model, name) for name in _TICKET_FIELDS}
    return DevTicket(
        **values, status=TicketStatus(model.status), depends_on=list(model.depends_on or [])
    )


def _event_to_domain(model: DevActivityEventModel) -> ActivityEvent:
    return ActivityEvent(
        project_id=model.project_id,
        actor_id=model.actor_id,
        actor_name=model.actor_name,
        actor_role=model.actor_role,
        kind=model.kind,
        summary=model.summary,
        ticket_id=model.ticket_id,
        detail=dict(model.detail or {}),
        sequence=model.sequence,
        created_at=model.created_at,
    )


class SQLAlchemyDevProjectStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self._event_locks: dict[str, asyncio.Lock] = {}

    async def save_project(self, project: DevProject) -> None:
        values = {name: getattr(project, name) for name in _PROJECT_FIELDS}
        async with self.session_factory() as session:
            await session.merge(
                DevProjectModel(
                    **values,
                    status=project.status.value,
                    usage=dict(project.usage),
                    members=list(project.members),
                )
            )
            await session.commit()

    async def get_project(self, project_id: str) -> DevProject | None:
        async with self.session_factory() as session:
            model = await session.get(DevProjectModel, project_id)
            return _project_to_domain(model) if model else None

    async def list_projects(self, tenant_id: str | None = None) -> list[DevProject]:
        stmt = select(DevProjectModel).order_by(DevProjectModel.created_at.desc())
        if tenant_id is not None:
            stmt = stmt.where(DevProjectModel.tenant_id == tenant_id)
        async with self.session_factory() as session:
            models = (await session.execute(stmt)).scalars().all()
            return [_project_to_domain(m) for m in models]

    async def save_ticket(self, ticket: DevTicket) -> None:
        values = {name: getattr(ticket, name) for name in _TICKET_FIELDS}
        async with self.session_factory() as session:
            await session.merge(
                DevTicketModel(
                    **values, status=ticket.status.value, depends_on=list(ticket.depends_on)
                )
            )
            await session.commit()

    async def list_tickets(self, project_id: str) -> list[DevTicket]:
        stmt = (
            select(DevTicketModel)
            .where(DevTicketModel.project_id == project_id)
            .order_by(DevTicketModel.sequence.asc())
        )
        async with self.session_factory() as session:
            models = (await session.execute(stmt)).scalars().all()
            return [_ticket_to_domain(m) for m in models]

    async def add_event(self, event: ActivityEvent) -> ActivityEvent:
        # Developers working in parallel write to the same feed. The lock orders writers in
        # this process; the unique constraint plus retry covers a second process.
        lock = self._event_locks.setdefault(event.project_id, asyncio.Lock())
        async with lock:
            for attempt in range(5):
                try:
                    return await self._insert_event(event)
                except IntegrityError:
                    if attempt == 4:
                        raise
        return event

    async def _insert_event(self, event: ActivityEvent) -> ActivityEvent:
        async with self.session_factory() as session:
            current = await session.scalar(
                select(func.max(DevActivityEventModel.sequence)).where(
                    DevActivityEventModel.project_id == event.project_id
                )
            )
            event.sequence = (current or 0) + 1
            session.add(
                DevActivityEventModel(
                    id=f"evt-{uuid.uuid4().hex[:16]}",
                    project_id=event.project_id,
                    sequence=event.sequence,
                    ticket_id=event.ticket_id,
                    actor_id=event.actor_id,
                    actor_name=event.actor_name,
                    actor_role=event.actor_role,
                    kind=event.kind,
                    summary=event.summary[:512],
                    detail=event.detail,
                    created_at=event.created_at,
                )
            )
            await session.commit()
        return event

    async def list_events(
        self, project_id: str, after: int = 0, limit: int = 200
    ) -> list[ActivityEvent]:
        stmt = (
            select(DevActivityEventModel)
            .where(
                DevActivityEventModel.project_id == project_id,
                DevActivityEventModel.sequence > after,
            )
            .order_by(DevActivityEventModel.sequence.asc())
            .limit(limit)
        )
        async with self.session_factory() as session:
            models = (await session.execute(stmt)).scalars().all()
            return [_event_to_domain(m) for m in models]

    async def set_ticket_approval(
        self, project_id: str, ticket_id: str, approval: str, feedback: str
    ) -> bool:
        """Record a human decision without rewriting fields the running team owns."""
        stmt = (
            update(DevTicketModel)
            .where(
                DevTicketModel.id == ticket_id,
                DevTicketModel.project_id == project_id,
                DevTicketModel.status == TicketStatus.AWAITING_APPROVAL.value,
            )
            .values(approval=approval, approval_feedback=feedback)
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            return bool(result.rowcount)

    async def set_members(self, project_id: str, members: list[dict[str, str]]) -> None:
        """Update only the team roster, leaving everything the running team writes alone."""
        async with self.session_factory() as session:
            await session.execute(
                update(DevProjectModel).where(DevProjectModel.id == project_id).values(members=members)
            )
            await session.commit()

    async def delete_project(self, project_id: str) -> None:
        async with self.session_factory() as session:
            # Explicit, so it does not depend on the database enforcing ON DELETE CASCADE
            await session.execute(
                delete(DevActivityEventModel).where(DevActivityEventModel.project_id == project_id)
            )
            await session.execute(delete(DevTicketModel).where(DevTicketModel.project_id == project_id))
            await session.execute(delete(DevProjectModel).where(DevProjectModel.id == project_id))
            await session.commit()
        self._event_locks.pop(project_id, None)

    async def mark_active_as_interrupted(self) -> list[str]:
        """
        Projects left PLANNING/RUNNING by a stopped process can no longer be progressing.
        Returns their ids, together with those that were waiting for quota.
        """
        active = [s.value for s in ACTIVE_PROJECT_STATUSES]
        resumable = [*active, ProjectStatus.WAITING_FOR_QUOTA.value]
        async with self.session_factory() as session:
            ids = list(
                (
                    await session.execute(
                        select(DevProjectModel.id).where(DevProjectModel.status.in_(resumable))
                    )
                ).scalars()
            )
            await session.execute(
                update(DevProjectModel)
                .where(DevProjectModel.status.in_(active))
                .values(status=ProjectStatus.INTERRUPTED.value)
            )
            await session.commit()
            return ids
