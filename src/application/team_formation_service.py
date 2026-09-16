"""
Team Formation & Dynamic Workforce Service.

Manages governed team formation, member allocations, cross-department teams,
temporary project teams, team lifecycle, and controlled employee provisioning under governance.
"""

import logging
import uuid
from datetime import UTC, datetime

from src.domain.employee import Employee, EmployeeStatus
from src.domain.events import (
    TeamDissolvedEvent,
    TeamFormedEvent,
    TeamMemberAddedEvent,
    WorkforceChangeRequestedEvent,
    WorkforceDecisionMadeEvent,
)
from src.domain.team import Team, TeamStatus, TeamType
from src.domain.workforce import (
    EmployeeTemplate,
    WorkforceAllocation,
    WorkforceChangeRequest,
    WorkforceChangeRequestStatus,
    WorkforceChangeRequestType,
    WorkforceDecision,
)
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.repositories.team_repository import SQLAlchemyTeamRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository

logger = logging.getLogger(__name__)


class TeamFormationService:
    def __init__(
        self,
        team_repo: SQLAlchemyTeamRepository,
        workforce_repo: SQLAlchemyWorkforceRepository,
        employee_repo: SQLAlchemyEmployeeRepository | None = None,
        outbox_repo: SQLAlchemyOutboxRepository | None = None,
    ) -> None:
        self.team_repo = team_repo
        self.workforce_repo = workforce_repo
        self.employee_repo = employee_repo
        self.outbox_repo = outbox_repo

    async def propose_team(
        self,
        name: str,
        code: str,
        purpose: str,
        team_type: TeamType = TeamType.TEMPORARY,
        project_id: str | None = None,
        department_ids: list[str] | None = None,
        manager_id: str | None = None,
        creation_reason: str = "",
    ) -> Team:
        existing = await self.team_repo.get_by_code(code)
        if existing:
            raise ValueError(f"Team with code '{code}' already exists")

        team = Team(
            name=name,
            code=code,
            purpose=purpose,
            team_type=team_type,
            project_id=project_id,
            department_ids=department_ids or [],
            manager_id=manager_id,
            status=TeamStatus.PROPOSED,
            creation_reason=creation_reason,
        )
        saved = await self.team_repo.save(team)

        if self.outbox_repo:
            evt = WorkforceChangeRequestedEvent(
                request_id=saved.id,
                request_type=WorkforceChangeRequestType.CREATE_TEAM.value,
                target_id=saved.id,
                requested_by_id=manager_id or "system",
            )
            await self.outbox_repo.save_event(evt)

        return saved

    async def request_workforce_change(
        self,
        request_type: WorkforceChangeRequestType,
        target_id: str,
        requested_by_id: str,
        justification: str,
    ) -> WorkforceChangeRequest:
        req = WorkforceChangeRequest(
            request_type=request_type,
            target_id=target_id,
            requested_by_id=requested_by_id,
            justification=justification,
            status=WorkforceChangeRequestStatus.PENDING,
        )
        saved = await self.workforce_repo.save_change_request(req)

        if self.outbox_repo:
            evt = WorkforceChangeRequestedEvent(
                request_id=saved.id,
                request_type=saved.request_type.value,
                target_id=saved.target_id,
                requested_by_id=saved.requested_by_id,
            )
            await self.outbox_repo.save_event(evt)

        return saved

    async def approve_workforce_change(
        self,
        change_request_id: str,
        actor_id: str,
        governance_approval_id: str | None = None,
        is_human_approval: bool = False,
        reason: str = "Approved by manager/governance",
    ) -> WorkforceDecision:
        req = await self.workforce_repo.get_change_request(change_request_id)
        if not req:
            raise ValueError(f"WorkforceChangeRequest '{change_request_id}' not found")

        if req.status != WorkforceChangeRequestStatus.PENDING:
            raise ValueError(f"Request is in status '{req.status}', cannot approve")

        # Consequential changes (e.g. REQUEST_NEW_EMPLOYEE, DISSOLVE_TEAM) require human approval or explicit governance approval ID
        if req.request_type in (WorkforceChangeRequestType.REQUEST_NEW_EMPLOYEE, WorkforceChangeRequestType.REQUEST_NEW_CAPABILITY):
            if not governance_approval_id and not is_human_approval:
                raise ValueError("Consequential workforce change requires explicit Human Governance approval")

        req.status = WorkforceChangeRequestStatus.APPROVED
        req.governance_approval_id = governance_approval_id
        req.processed_at = datetime.now(UTC)
        await self.workforce_repo.save_change_request(req)

        decision = WorkforceDecision(
            change_request_id=req.id,
            actor_id=actor_id,
            human_approver_id=actor_id if is_human_approval else None,
            decision_type="APPROVED",
            reason=reason,
            policy_applied="WORKFORCE_GOVERNANCE_POLICY_V1",
        )
        saved_decision = await self.workforce_repo.save_decision(decision)

        if self.outbox_repo:
            evt = WorkforceDecisionMadeEvent(
                decision_id=saved_decision.id,
                change_request_id=req.id,
                actor_id=actor_id,
                decision_type="APPROVED",
            )
            await self.outbox_repo.save_event(evt)

        return saved_decision

    async def form_team(
        self,
        team_id: str,
        member_employees: list[tuple[Employee, str, float]],  # (employee, role, allocation_pct)
        manager_id: str | None = None,
    ) -> Team:
        team = await self.team_repo.get_by_id(team_id)
        if not team:
            raise ValueError(f"Team '{team_id}' not found")

        if manager_id:
            team.manager_id = manager_id

        team.activate()

        derived_capabilities: set[str] = set()

        for emp, role_in_team, alloc_pct in member_employees:
            if not emp.is_executable():
                raise ValueError(f"Cannot assign inactive/suspended employee {emp.name} ({emp.id})")
            team.add_member(
                employee_id=emp.id,
                role_in_team=role_in_team,
                allocation_percentage=alloc_pct,
            )
            derived_capabilities.update(c.name if hasattr(c, "name") else str(c) for c in emp.capabilities)

            # Create temporary WorkforceAllocation
            alloc = WorkforceAllocation(
                employee_id=emp.id,
                team_id=team.id,
                project_id=team.project_id,
                department_id=emp.department_id,
                allocation_percentage=alloc_pct,
                is_temporary=True,
                status="ACTIVE",
            )
            await self.workforce_repo.save_allocation(alloc)

            if self.outbox_repo:
                evt = TeamMemberAddedEvent(
                    team_id=team.id,
                    employee_id=emp.id,
                    role_in_team=role_in_team,
                    allocation_percentage=alloc_pct,
                )
                await self.outbox_repo.save_event(evt)

        team.capabilities = sorted(list(derived_capabilities))
        saved_team = await self.team_repo.save(team)

        if self.outbox_repo:
            formed_evt = TeamFormedEvent(
                team_id=saved_team.id,
                team_name=saved_team.name,
                team_type=saved_team.team_type.value,
                manager_id=saved_team.manager_id,
                member_count=len(saved_team.members),
            )
            await self.outbox_repo.save_event(formed_evt)

        return saved_team

    async def dissolve_team(self, team_id: str, reason: str = "Objective completed") -> Team:
        team = await self.team_repo.get_by_id(team_id)
        if not team:
            raise ValueError(f"Team '{team_id}' not found")

        team.start_dissolving()
        for member in team.members:
            if member.removed_at is None:
                member.removed_at = datetime.now(UTC)

        team.dissolve()
        saved = await self.team_repo.save(team)

        # Deactivate temporary workforce allocations for this team
        allocations = await self.workforce_repo.list_allocations()
        for a in allocations:
            if a.team_id == team_id and a.status == "ACTIVE":
                a.status = "COMPLETED"
                a.end_time = datetime.now(UTC)
                await self.workforce_repo.save_allocation(a)

        if self.outbox_repo:
            evt = TeamDissolvedEvent(
                team_id=saved.id,
                reason=reason,
            )
            await self.outbox_repo.save_event(evt)

        return saved

    async def provision_employee_with_governance(
        self,
        template: EmployeeTemplate,
        name: str,
        department_id: str,
        manager_id: str | None = None,
        governance_approval_id: str | None = None,
        is_human_approved: bool = False,
    ) -> Employee:
        """
        Controlled employee provisioning.
        Requires explicit Governance approval or human approval.
        Creates Employee entity linked to template capabilities.
        """
        if not self.employee_repo:
            raise ValueError("Employee repository is not configured for provisioning")

        if not governance_approval_id and not is_human_approved:
            raise ValueError("Autonomous employee provisioning prohibited! Requires Human Governance approval.")

        # Create new Employee
        code_suffix = str(uuid.uuid4())[:6].upper()
        emp_code = f"EMP-{template.role}-{code_suffix}"

        # Determine role string
        role_str = template.role or "Engineer"

        from src.domain.employee import EmployeeCapability, EmployeeSkill

        new_emp = Employee(
            id=str(uuid.uuid4()),
            employee_code=emp_code,
            name=name,
            title=template.title,
            role=role_str,
            agent_id=f"agent-{uuid.uuid4()}",
            department_id=department_id,
            manager_id=manager_id,
            status=EmployeeStatus.ACTIVE,
            capabilities=[EmployeeCapability(name=c) for c in template.capabilities],
            skills=[EmployeeSkill(name=s) for s in template.skills],
        )
        saved_emp = await self.employee_repo.save(new_emp)

        return saved_emp
