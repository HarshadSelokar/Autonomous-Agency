"""Phase 15 Dynamic Workforce, Capability-Based Staffing & Autonomous Team Formation E2E Demo Script.

Demonstrates:
Company Objective -> Project -> Task Graph -> Capability Demand -> Capacity Analysis ->
Capability Gap -> Staffing Recommendation -> Governance Approval -> Team Formation ->
Employee Allocation -> Task Assignment -> Verification -> Completion.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.team_formation_service import TeamFormationService
from src.application.workforce_planning_service import WorkforcePlanningService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.team import TeamType
from src.domain.workforce import (
    EmployeeTemplate,
    WorkforceChangeRequestType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.repositories.team_repository import SQLAlchemyTeamRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DemoDynamicWorkforce")


async def run_demo():
    logger.info("==========================================================================")
    logger.info("STARTING PHASE 15 DYNAMIC WORKFORCE & TEAM FORMATION DEMO")
    logger.info("==========================================================================")

    # 1. Database setup
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        wf_repo = SQLAlchemyWorkforceRepository(session)
        team_repo = SQLAlchemyTeamRepository(session)
        emp_repo = SQLAlchemyEmployeeRepository(session)
        outbox_repo = SQLAlchemyOutboxRepository(session)

        wf_service = WorkforcePlanningService(workforce_repo=wf_repo, outbox_repo=outbox_repo)
        team_service = TeamFormationService(
            team_repo=team_repo,
            workforce_repo=wf_repo,
            employee_repo=emp_repo,
            outbox_repo=outbox_repo,
        )

        # 2. Seed Initial Workforce
        logger.info("\n--- 1. SEEDING INITIAL WORKFORCE ---")
        emp1 = Employee(
            id="emp-alice",
            employee_code="EMP-001",
            name="Alice Backend Lead",
            title="Senior Backend Engineer",
            role="ENGINEER",
            agent_id="agent-alice",
            status=EmployeeStatus.ACTIVE,
            capabilities=["BACKEND_DEVELOPMENT", "API_DESIGN"],
        )
        emp2 = Employee(
            id="emp-bob",
            employee_code="EMP-002",
            name="Bob Frontend Lead",
            title="Senior Frontend Engineer",
            role="ENGINEER",
            agent_id="agent-bob",
            status=EmployeeStatus.ACTIVE,
            capabilities=["FRONTEND_DEVELOPMENT"],
        )
        await emp_repo.save(emp1)
        await emp_repo.save(emp2)
        logger.info("Seeded Employees: Alice (BACKEND_DEVELOPMENT), Bob (FRONTEND_DEVELOPMENT)")

        # 3. Work Demand Creation
        logger.info("\n--- 2. ANALYZING WORK DEMAND ---")
        demand_backend = await wf_service.create_workforce_demand(
            source_type="PROJECT",
            source_id="proj-phoenix",
            capability="BACKEND_DEVELOPMENT",
            required_count=1,
            priority=4,
        )
        demand_sec = await wf_service.create_workforce_demand(
            source_type="PROJECT",
            source_id="proj-phoenix",
            capability="SECURITY",
            required_count=1,
            priority=5,
            governance_required=True,
        )
        logger.info(f"Created Demand: 1 x BACKEND_DEVELOPMENT (ID: {demand_backend.id})")
        logger.info(f"Created Demand: 1 x SECURITY (ID: {demand_sec.id})")

        # 4. Capacity Snapshots & Gap Analysis
        logger.info("\n--- 3. CALCULATING CAPACITY SNAPSHOTS & DETECTING GAPS ---")
        emps = await emp_repo.list_all()
        snapshots = await wf_service.calculate_capacity_snapshots(employees=emps)
        logger.info(f"Generated {len(snapshots)} capacity snapshots.")

        gaps = await wf_service.detect_capability_gaps()
        logger.info(f"Detected {len(gaps)} capability gap(s):")
        for g in gaps:
            logger.info(f"  - Capability: {g.capability}, Gap Count: {g.gap_count}, Severity: {g.severity.value}")

        # 5. Staffing Recommendation for Backend
        logger.info("\n--- 4. GENERATING STAFFING RECOMMENDATIONS ---")
        rec_backend = await wf_service.generate_staffing_recommendation(
            demand=demand_backend,
            all_employees=emps,
        )
        logger.info(f"Backend Recommendation Score: {rec_backend.final_score}")
        logger.info(f"Selected Candidates: {rec_backend.candidate_employee_ids}")

        # 6. Governed Employee Provisioning for Missing Security Capability
        logger.info("\n--- 5. GOVERNED EMPLOYEE PROVISIONING FOR MISSING CAPABILITY ---")
        sec_change_req = await team_service.request_workforce_change(
            request_type=WorkforceChangeRequestType.REQUEST_NEW_EMPLOYEE,
            target_id="template-security-eng",
            requested_by_id="mgr-1",
            justification="Security capability gap detected for Project Phoenix",
        )
        logger.info(f"Created Workforce Change Request (ID: {sec_change_req.id}, Status: {sec_change_req.status.value})")

        # Approve change request under Human Governance
        decision = await team_service.approve_workforce_change(
            change_request_id=sec_change_req.id,
            actor_id="human-governance-officer",
            is_human_approval=True,
            reason="Approved critical security hiring for Project Phoenix",
        )
        logger.info(f"Governance Decision: {decision.decision_type} by {decision.human_approver_id}")

        # Provision Security Employee
        sec_template = EmployeeTemplate(
            title="Security Specialist",
            role="ENGINEER",
            capabilities=["SECURITY"],
            skills=["Pentesting", "Threat Modeling"],
        )
        new_sec_emp = await team_service.provision_employee_with_governance(
            template=sec_template,
            name="Charlie Security Specialist",
            department_id="dept-eng",
            is_human_approved=True,
        )
        logger.info(f"Provisioned Employee: {new_sec_emp.name} (Code: {new_sec_emp.employee_code})")

        # 7. Dynamic Team Formation
        logger.info("\n--- 6. DYNAMIC TEAM FORMATION & ALLOCATION ---")
        team = await team_service.propose_team(
            name="Project Phoenix Strike Team",
            code="PHX-STRIKE",
            purpose="Execute core backend and security review for Project Phoenix",
            team_type=TeamType.PROJECT,
            project_id="proj-phoenix",
            manager_id="mgr-1",
            creation_reason="Dynamic cross-functional project team formation",
        )
        logger.info(f"Proposed Team: {team.name} (Code: {team.code}, Status: {team.status.value})")

        formed_team = await team_service.form_team(
            team_id=team.id,
            member_employees=[
                (emp1, "BACKEND_LEAD", 50.0),
                (new_sec_emp, "SECURITY_LEAD", 100.0),
            ],
            manager_id="mgr-1",
        )
        logger.info(f"Formed Active Team! Members Count: {len(formed_team.members)}")
        logger.info(f"Derived Team Capabilities: {formed_team.capabilities}")

        # 8. Team Dissolution upon Project Completion
        logger.info("\n--- 7. PROJECT COMPLETION & TEAM DISSOLUTION ---")
        dissolved = await team_service.dissolve_team(
            team_id=formed_team.id,
            reason="Project Phoenix successfully delivered and verified",
        )
        logger.info(f"Team Status: {dissolved.status.value}, Dissolved At: {dissolved.dissolved_at}")
        logger.info("Temporary allocations released. Employees returned to home department assignments.")

    await engine.dispose()

    logger.info("==========================================================================")
    logger.info("PHASE 15 DYNAMIC WORKFORCE DEMO COMPLETED SUCCESSFULLY!")
    logger.info("==========================================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())
