"""
Phase 5 Communication & Collaboration Protocol End-to-End Demonstration Script.
Demonstrates structured conversations, task-linked blockers, manager escalations,
delivery state acknowledgements, and prompt security context building.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.models  # noqa: F401
from src.application.communication_service import CommunicationService
from src.application.message_context_builder import MessageContextBuilder
from src.application.message_delivery_service import MessageDeliveryService
from src.application.message_router import MessageRouter
from src.domain.conversation import ConversationType
from src.domain.employee import Employee, EmployeeStatus
from src.domain.message import MessageType
from src.infrastructure.database import Base
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.conversation_repository import (
    SQLAlchemyConversationRepository,
)
from src.infrastructure.repositories.employee_repository import (
    SQLAlchemyEmployeeRepository,
)
from src.infrastructure.repositories.message_repository import (
    SQLAlchemyMessageRepository,
)
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository


async def run_communication_demo() -> None:
    print("=" * 70)
    print("AUTONOMOUS AI COMPANY PLATFORM — PHASE 5 COMMUNICATION DEMO")
    print("=" * 70)

    # 1. Setup in-memory SQLite database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Repositories
        emp_repo = SQLAlchemyEmployeeRepository(session)
        agent_repo = SQLAlchemyAgentRepository(session)
        conv_repo = SQLAlchemyConversationRepository(session)
        msg_repo = SQLAlchemyMessageRepository(session)
        outbox_repo = SQLAlchemyOutboxRepository(session)

        # Services
        router = MessageRouter(
            employee_repository=emp_repo,
            agent_repository=agent_repo,
            conversation_repository=conv_repo,
        )
        delivery_service = MessageDeliveryService(
            message_repository=msg_repo,
            outbox_repository=outbox_repo,
        )
        comm_service = CommunicationService(
            conversation_repository=conv_repo,
            message_repository=msg_repo,
            message_router=router,
            message_delivery_service=delivery_service,
        )
        context_builder = MessageContextBuilder(message_repository=msg_repo)

        # 2. Seed Employees and Agents (Enforcing EMPLOYEE != AGENT != LLM)
        from src.domain.agent import Agent
        ag_researcher = Agent(id="agent-researcher", name="Alice Research Agent", role="Researcher")
        ag_manager = Agent(id="agent-manager", name="Bob Manager Agent", role="Manager")
        ag_director = Agent(id="agent-director", name="Carol Director Agent", role="Director")

        for ag in [ag_researcher, ag_manager, ag_director]:
            await agent_repo.save(ag)

        alice = Employee(
            id="emp-alice",
            employee_code="E01",
            name="Alice Smith",
            title="Senior Research Engineer",
            role="IC",
            agent_id="agent-researcher",
            status=EmployeeStatus.ACTIVE,
        )
        bob = Employee(
            id="emp-bob",
            employee_code="E02",
            name="Bob Jones",
            title="Engineering Manager",
            role="Manager",
            agent_id="agent-manager",
            status=EmployeeStatus.ACTIVE,
        )
        carol = Employee(
            id="emp-carol",
            employee_code="E03",
            name="Carol Danvers",
            title="Director of Engineering",
            role="Director",
            agent_id="agent-director",
            status=EmployeeStatus.ACTIVE,
        )

        for emp in [alice, bob, carol]:
            await emp_repo.save(emp)
        await session.commit()

        print("\n--- STEP 1: Created Organizational Identities (EMPLOYEE != AGENT != LLM) ---")
        print(f"  Alice: ID='{alice.id}', Role='{alice.role}', Agent='{alice.agent_id}'")
        print(f"  Bob:   ID='{bob.id}', Role='{bob.role}', Agent='{bob.agent_id}'")
        print(f"  Carol: ID='{carol.id}', Role='{carol.role}', Agent='{carol.agent_id}'")

        # 3. Create Team Conversation
        conv_team = await comm_service.create_conversation(
            title="Analytics Platform Architecture",
            conversation_type=ConversationType.TEAM,
            created_by_employee_id="emp-bob",
            participant_employee_ids=["emp-alice", "emp-carol"],
        )
        print(f"\n--- STEP 2: Created Team Conversation '{conv_team.title}' (ID: {conv_team.id}) ---")

        # 4. Exchange Messages
        msg1 = await comm_service.send_message(
            sender_employee_id="emp-bob",
            conversation_id=conv_team.id,
            message_type=MessageType.REQUEST,
            subject="Architecture Specs",
            content="Alice, please draft the data pipeline architecture specification.",
        )
        print(f"  Bob -> Team: [{msg1.message_type.value}] '{msg1.subject}' (Delivery: {msg1.delivery_state.value})")

        msg2 = await comm_service.reply_to_message(
            original_message_id=msg1.id,
            sender_employee_id="emp-alice",
            content="Working on the spec now. Will update by end of day.",
            sender_agent_id="agent-researcher",
            sender_run_id="run-101",
        )
        print(f"  Alice -> Bob (Reply): [{msg2.message_type.value}] '{msg2.content}'")

        # 5. Report Blocker on Task T-100
        print("\n--- STEP 3: Reporting Task Blocker (Task T-100) ---")
        msg_blocker = await comm_service.report_blocker(
            sender_employee_id="emp-alice",
            task_id="T-100",
            blocker_description="Database credentials for PostgreSQL analytics cluster are missing.",
            manager_employee_id="emp-bob",
            sender_agent_id="agent-researcher",
            sender_run_id="run-102",
        )
        print(f"  Alice -> Bob: [BLOCKER] Task T-100: '{msg_blocker.content}'")

        # 6. Bob Acknowledges Blocker and Escalates to Carol
        print("\n--- STEP 4: Manager Acknowledgement & Escalation ---")
        ack_msg = await delivery_service.acknowledge_message(msg_blocker.id, participant_id="emp-bob")
        print(f"  Bob Acknowledged Blocker message (Delivery State: {ack_msg.delivery_state.value})")

        msg_escalation = await comm_service.escalate_blocker(
            sender_manager_id="emp-bob",
            task_id="T-100",
            original_blocker_message_id=msg_blocker.id,
            higher_manager_id="emp-carol",
            escalation_reason="Production database credentials require Director approval.",
        )
        print(f"  Bob -> Carol: [ESCALATION] '{msg_escalation.content}'")

        # 7. Process Transactional Outbox Worker Pass
        print("\n--- STEP 5: Transactional Outbox Processing Pass ---")
        processed_count = await delivery_service.process_outbox_queue()
        print(f"  Outbox Worker processed {processed_count} queued events successfully.")

        # 8. Agent Context Building with Prompt Security Boundaries
        print("\n--- STEP 6: Agent Context Builder & Prompt Security Framing ---")
        relevant_msgs = await context_builder.build_task_communication_context(task_id="T-100")
        prompt_context = context_builder.format_messages_for_agent_prompt(relevant_msgs)
        print(prompt_context)

        print("\n" + "=" * 70)
        print("COMMUNICATION PROTOCOL DEMONSTRATION COMPLETE — 100% SUCCESS")
        print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_communication_demo())
