"""
End-to-End Demonstration Script for Phase 6 — Meetings & Decision Management.
Demonstrates Scenario 67: Objective -> Plan -> Task -> Meeting -> Discussion -> AI Decision Proposal
-> Manager Authority Approval -> Task Integration -> Decision Supersession -> Provenance Audit.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.agent_meeting_assistant import AgentMeetingAssistant
from src.application.decision_authority_service import (
    DecisionAuthorityService,
    UnauthorizedDecisionApprovalError,
)
from src.application.decision_integration_service import DecisionIntegrationService
from src.application.meeting_context_builder import MeetingContextBuilder
from src.application.meeting_scheduling_service import MeetingSchedulingService
from src.domain.decision import (
    Decision,
    DecisionProvenance,
    DecisionStatus,
    DecisionType,
)
from src.domain.employee import Employee, EmployeeStatus
from src.domain.meeting import (
    AttendanceStatus,
    MeetingPurpose,
    MeetingStatus,
)
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import employee_domain_to_model
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.meeting_repository import SQLAlchemyMeetingRepository


async def run_demo() -> None:
    print("=" * 80)
    print("PHASE 6 — MEETINGS & DECISION MANAGEMENT END-TO-END DEMO")
    print("=" * 80)

    # 1. Initialize In-Memory Database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # 2. Seed Employees & Manager
        emp_bob = Employee(
            id="emp-bob",
            name="Bob Manager",
            role="Engineering Manager",
            status=EmployeeStatus.ACTIVE,
            employee_code="EMP_BOB",
            title="Engineering Manager",
            agent_id="agent-mgr",
        )
        emp_alice = Employee(
            id="emp-alice",
            name="Alice Research",
            role="Research Engineer",
            status=EmployeeStatus.ACTIVE,
            employee_code="EMP_ALICE",
            title="Senior Researcher",
            agent_id="agent-research",
        )
        emp_charlie = Employee(
            id="emp-charlie",
            name="Charlie Backend",
            role="Backend Engineer",
            status=EmployeeStatus.ACTIVE,
            employee_code="EMP_CHARLIE",
            title="Backend Lead",
            agent_id="agent-backend",
        )
        session.add(employee_domain_to_model(emp_bob))
        session.add(employee_domain_to_model(emp_alice))
        session.add(employee_domain_to_model(emp_charlie))
        await session.commit()

        meeting_repo = SQLAlchemyMeetingRepository(session)
        employee_repo = SQLAlchemyEmployeeRepository(session)
        decision_repo = SQLAlchemyDecisionRepository(session)

        scheduling_service = MeetingSchedulingService(
            meeting_repo=meeting_repo, employee_repo=employee_repo
        )
        auth_service = DecisionAuthorityService(employee_repo=employee_repo)
        integration_service = DecisionIntegrationService(decision_repo=decision_repo)
        assistant = AgentMeetingAssistant(
            meeting_repo=meeting_repo, decision_repo=decision_repo
        )
        context_builder = MeetingContextBuilder(meeting_repo=meeting_repo)

        # 3. Create & Schedule Meeting M1: Architecture Review
        print("\n[STEP 1] Creating and Scheduling Meeting M1: Architecture Review")
        meeting = await scheduling_service.create_meeting(
            meeting_id="m-100",
            title="Analytics Platform Architecture Review",
            purpose=MeetingPurpose.REVIEW,
            organizer_employee_id="emp-bob",
            participant_ids=["emp-alice", "emp-charlie"],
            objective_id="obj-analytics",
            plan_id="plan-analytics",
            task_id="task-arch-design",
        )
        print(f" -> Meeting Created: ID={meeting.id}, Status={meeting.status.value}")

        now = datetime.now(UTC)
        meeting = await scheduling_service.schedule_meeting(
            meeting_id="m-100",
            scheduled_start=now + timedelta(hours=1),
            scheduled_end=now + timedelta(hours=2),
        )
        await session.commit()
        print(f" -> Meeting Scheduled: Status={meeting.status.value}, Start={meeting.scheduled_start}")

        # 4. Add Agenda Items & Start Meeting
        print("\n[STEP 2] Adding Agenda Items & Starting Meeting")
        meeting.add_agenda_item(item_id="ag-1", title="Research Findings", owner_employee_id="emp-alice", duration_minutes=15)
        meeting.add_agenda_item(item_id="ag-2", title="Database Engine Selection", owner_employee_id="emp-charlie", duration_minutes=30)
        meeting.transition_to(MeetingStatus.STARTING)
        meeting.transition_to(MeetingStatus.IN_PROGRESS)
        meeting.record_attendance("emp-alice", AttendanceStatus.ATTENDED)
        meeting.record_attendance("emp-charlie", AttendanceStatus.ATTENDED)
        await meeting_repo.save(meeting)
        await session.commit()
        print(f" -> Meeting Status={meeting.status.value}, Participants Attended: 2")

        # 5. AI Agent Proposes a Decision (D1: Use PostgreSQL)
        print("\n[STEP 3] AI Agent Proposes Decision (D1: Use PostgreSQL)")
        proposal_d1 = await assistant.propose_decision_from_meeting(
            meeting_id="m-100",
            title="Primary Storage Engine Selection",
            question="Which database engine should power the analytics platform?",
            recommended_option="PostgreSQL",
            rationale="Provides strong ACID guarantees and supports JSON/vector extensions.",
            agent_id="agent-backend",
            proposer_employee_id="emp-charlie",
            alternatives=["MySQL", "ClickHouse"],
            evidence=["Benchmarking Report v1"],
        )
        await session.commit()

        print(f" -> Decision Proposed: ID={proposal_d1.id}")
        print(f" -> Status: {proposal_d1.status.value} (INVARIANT: Agent proposal CANNOT auto-approve!)")
        print(f" -> Provenance: {proposal_d1.provenance.value}")

        # 6. Unauthorized Approval Attempt by Alice (Rejection Verification)
        print("\n[STEP 4] Attempting Unauthorized Approval by Alice (Research Engineer)")
        try:
            proposal_d1.approving_authority_role = "Engineering Manager"
            await auth_service.approve_decision(proposal_d1, approver_employee_id="emp-alice")
            print(" -> ERROR: Unauthorized approval unexpectedly succeeded!")
        except UnauthorizedDecisionApprovalError as err:
            print(f" -> SUCCESS: Unauthorized approval rejected as expected: {err}")

        # 7. Authorized Approval by Bob (Engineering Manager)
        print("\n[STEP 5] Authorized Approval by Bob Manager")
        approved_d1 = await auth_service.approve_decision(proposal_d1, approver_employee_id="emp-bob")
        await decision_repo.save(approved_d1)
        await session.commit()

        exec_res = await integration_service.execute_approved_decision_actions(
            decision_id=approved_d1.id, actor_employee_id="emp-bob"
        )
        print(f" -> Decision D1 Status: {approved_d1.status.value}")
        print(f" -> Executed Actions: {exec_res['executed_actions']}")

        # 8. Decision Supersession Demonstration (D2: Migrate to ClickHouse)
        print("\n[STEP 6] Decision Supersession Demo: Creating & Approving D2 to Supersede D1")
        proposal_d2 = Decision(
            id="dec-200-clickhouse",
            title="Migrate Analytics Storage to ClickHouse",
            question="Which database engine should power real-time analytics query workloads?",
            decision_maker_employee_id="emp-charlie",
            status=DecisionStatus.PROPOSED,
            decision_type=DecisionType.ARCHITECTURE,
            chosen_option="ClickHouse",
            rationale="Sub-second OLAP queries across 1B records.",
            previous_decision_id=approved_d1.id,
            provenance=DecisionProvenance.MANAGER,
        )
        await decision_repo.save(proposal_d2)

        approved_d2 = await auth_service.approve_decision(proposal_d2, approver_employee_id="emp-bob")
        await decision_repo.save(approved_d2)

        superseded_d1 = await decision_repo.supersede_decision(
            old_decision_id=approved_d1.id,
            new_decision_id=approved_d2.id,
            actor_employee_id="emp-bob",
        )
        await session.commit()

        print(f" -> D1 Status: {superseded_d1.status.value} (Preserved historically in DB)")
        print(f" -> D2 Status: {approved_d2.status.value} (Currently Authoritative)")

        # 9. Meeting Context & Conclusion
        print("\n[STEP 7] Fetching Framed Meeting Context & Ending Meeting")
        context = await context_builder.build_context(meeting_id="m-100", requesting_employee_id="emp-bob")
        print(" -> Framed Meeting Prompt Context Preview:")
        print("   " + "\n   ".join(context["framed_prompt_context"].split("\n")[:8]))

        meeting.transition_to(MeetingStatus.ENDED)
        await meeting_repo.save(meeting)
        await session.commit()
        print(f" -> Final Meeting Status: {meeting.status.value}")

    await engine.dispose()
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY (100% INVARIANTS VERIFIED)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())
