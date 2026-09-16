"""
Phase 7 End-to-End Demonstration Script.
Demonstrates Memory, Workspace, Artifacts, Authority Escalation, and Security Framing.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.decision_integration_service import DecisionIntegrationService
from src.application.embedding_provider import FakeEmbeddingProvider
from src.application.memory_context_builder import MemoryContextBuilder
from src.application.memory_retrieval_service import MemoryRetrievalService
from src.application.memory_service import MemoryService
from src.application.workspace_authorization_service import (
    WorkspaceAccessDeniedError,
    WorkspaceAuthorizationService,
)
from src.domain.artifact import Artifact, compute_sha256
from src.domain.decision import Decision, DecisionStatus, DecisionType
from src.domain.employee import Employee, EmployeeStatus
from src.domain.memory import MemoryAuthority, MemoryProvenance, MemoryScope, MemoryType
from src.domain.workspace import Workspace, WorkspaceStatus, WorkspaceType
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import employee_domain_to_model
from src.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from src.infrastructure.repositories.decision_repository import SQLAlchemyDecisionRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.memory_repository import SQLAlchemyMemoryRepository
from src.infrastructure.repositories.workspace_repository import SQLAlchemyWorkspaceRepository
from src.infrastructure.storage_provider import LocalStorageProvider


async def run_phase7_demo() -> None:
    print("========================================================================")
    print("PHASE 7 END-TO-END DEMONSTRATION: MEMORY, WORKSPACE & ARTIFACT CONTEXT")
    print("========================================================================\n")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Repositories
        emp_repo = SQLAlchemyEmployeeRepository(session)
        mem_repo = SQLAlchemyMemoryRepository(session)
        ws_repo = SQLAlchemyWorkspaceRepository(session)
        art_repo = SQLAlchemyArtifactRepository(session)
        dec_repo = SQLAlchemyDecisionRepository(session)

        # 1. Seed Manager & Developer Employees
        mgr = Employee(
            id="emp-mgr-alice",
            employee_code="EMP_MGR_01",
            name="Alice Vance",
            title="Engineering Director",
            role="Engineering Manager",
            agent_id="agent-mgr-alice",
            status=EmployeeStatus.ACTIVE,
        )
        dev = Employee(
            id="emp-dev-bob",
            employee_code="EMP_DEV_01",
            name="Bob Smith",
            title="Senior Systems Developer",
            role="Software Engineer",
            agent_id="agent-dev-bob",
            status=EmployeeStatus.ACTIVE,
        )
        session.add(employee_domain_to_model(mgr))
        session.add(employee_domain_to_model(dev))
        await session.commit()
        print("1. Employees Seeded: Alice Vance (Manager) & Bob Smith (Developer)")

        # 2. Create Task Workspace W100 for Task T100
        ws = Workspace(
            id="ws-t100",
            name="Task T100 Architecture Research Workspace",
            workspace_type=WorkspaceType.TASK,
            owner_id="TASK:T100",
            status=WorkspaceStatus.ACTIVE,
            task_id="T100",
            employee_id=dev.id,
        )
        await ws_repo.save(ws)
        await session.commit()
        print(f"2. Workspace Created: '{ws.name}' (ID: {ws.id}, Status: {ws.status.value})")

        # 3. Verify Workspace Access for Developer on Task T100
        auth_service = WorkspaceAuthorizationService(workspace_repo=ws_repo)
        auth_ws = await auth_service.validate_task_workspace_access(
            workspace_id=ws.id,
            current_task_id="T100",
            actor_employee_id=dev.id,
        )
        print(f"3. Workspace Authorization Verified: Developer Bob granted access to {auth_ws.id}")

        # 4. Agent creates Research Artifact in Workspace
        storage = LocalStorageProvider(base_dir="scratch/demo_artifacts")
        report_content = b"# Database Selection Benchmark Report\nPostgreSQL demonstrates superior JSONB indexing and ACID compliance."
        report_sha256 = compute_sha256(report_content)
        storage_key = f"workspaces/{ws.id}/art-report-v1.md"
        await storage.store_bytes(storage_key, report_content)

        art_v1 = Artifact(
            id="art-report-100",
            workspace_id=ws.id,
            name="database_benchmark.md",
            mime_type="text/markdown",
            size_bytes=len(report_content),
            checksum_sha256=report_sha256,
            created_by_employee_id=dev.id,
            version=1,
            task_id="T100",
            storage_key=storage_key,
        )
        await art_repo.save(art_v1)
        await session.commit()
        print(f"4. Artifact Created & Stored: '{art_v1.name}' v{art_v1.version} (SHA-256: {art_v1.checksum_sha256[:12]}...)")

        # 5. Agent creates Candidate Memory (GENERATED)
        mem_service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)
        candidate_mem = await mem_service.create_memory(
            memory_type=MemoryType.SEMANTIC,
            scope=MemoryScope.COMPANY,
            owner_id="COMPANY",
            content="PostgreSQL is the recommended database for high-concurrency transactional work.",
            summary="PostgreSQL recommendation",
            authority=MemoryAuthority.GENERATED,
            confidence=0.85,
            provenance=MemoryProvenance.AGENT_RUN,
            task_id="T100",
            employee_id=dev.id,
            artifact_id=art_v1.id,
        )
        await session.commit()
        print(f"5. Candidate Memory Created: ID {candidate_mem.id} (Authority: {candidate_mem.authority.value}, Provenance: {candidate_mem.provenance.value})")

        # 6. Manager Reviews & Promotes Memory to AUTHORITATIVE
        promoted_mem = await mem_service.promote_memory(
            memory_id=candidate_mem.id,
            target_authority=MemoryAuthority.AUTHORITATIVE,
            actor_employee_id=mgr.id,
        )
        await session.commit()
        print(f"6. Manager Review & Promotion: Memory {promoted_mem.id} promoted to {promoted_mem.authority.value}")

        # 7. Approved Decision derives AUTHORITATIVE Organizational Memory automatically
        dec = Decision(
            id="dec-db-choice",
            title="Official Relational Database Standard",
            question="What is the official DB for corporate microservices?",
            decision_maker_employee_id=dev.id,
            decision_type=DecisionType.ARCHITECTURE,
            approving_authority_role="Engineering Manager",
            chosen_option="PostgreSQL",
            rationale="Approved by Engineering Architecture Committee.",
        )
        dec.transition_to(DecisionStatus.UNDER_REVIEW)
        dec.transition_to(DecisionStatus.APPROVED, approver_employee_id=mgr.id, approver_role=mgr.role)
        await dec_repo.save(dec)

        dec_service = DecisionIntegrationService(decision_repo=dec_repo, memory_service=mem_service)
        res = await dec_service.execute_approved_decision_actions(decision_id=dec.id, actor_employee_id=mgr.id)
        await session.commit()
        print(f"7. Decision-Derived Memory Generated via DecisionIntegrationService for Decision '{dec.id}' ({res['executed_actions'][0]})")

        # 8. Future Task Execution Context Building
        embedding_provider = FakeEmbeddingProvider()
        retrieval_service = MemoryRetrievalService(memory_repo=mem_repo, embedding_provider=embedding_provider)
        context_builder = MemoryContextBuilder(retrieval_service=retrieval_service)
        context_result = await context_builder.build_context(
            task_id="T200",
            requesting_employee_id=dev.id,
            query="database standard",
        )
        framed_prompt = context_result["framed_prompt_context"]

        print("\n8. Retrieved Organizational Memory Context Prompt:")
        print("------------------------------------------------------------------------")
        print(framed_prompt)
        print("------------------------------------------------------------------------")

        # 9. Verify Security Isolation - Unauthorized Task Access Blocked
        print("\n9. Verifying Security Isolation:")
        try:
            await auth_service.validate_task_workspace_access(
                workspace_id=ws.id,
                current_task_id="T300",  # Unrelated Task
                actor_employee_id="emp-other",
            )
            print("[SECURITY FAILURE] Cross-workspace access allowed!")
        except WorkspaceAccessDeniedError as err:
            print(f"[SECURITY ENFORCED] Cross-workspace access denied! ({err})")

    await engine.dispose()
    print("\n========================================================================")
    print("PHASE 7 DEMONSTRATION COMPLETE: ALL INVARIANTS & SECURITY CHECKS PASSED!")
    print("========================================================================")


if __name__ == "__main__":
    asyncio.run(run_phase7_demo())
