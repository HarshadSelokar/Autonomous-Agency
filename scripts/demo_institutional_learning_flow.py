"""Phase 18 Autonomous Knowledge, Organizational Memory & Institutional Learning E2E Demo Script.

Demonstrates:
Raw Task Failure -> Failure Learning -> Candidate Knowledge -> Independent Evidence Validation ->
Authority Promotion -> Conflict Detection & Resolution -> Versioned Procedure -> Phase 11 Governance Approval ->
Isolated Organizational Experiment -> Experiment Promotion -> Knowledge Retrieval & Security Framing.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.institutional_learning_service import InstitutionalLearningService
from src.application.knowledge_validation_service import KnowledgeValidationService
from src.application.memory_context_builder import MemoryContextBuilder
from src.application.memory_retrieval_service import MemoryRetrievalService
from src.application.organizational_experiment_service import OrganizationalExperimentService
from src.application.procedure_management_service import ProcedureManagementService
from src.domain.experiment import ExperimentStatus
from src.domain.knowledge import ConflictStatus, KnowledgeAuthority, KnowledgeItem, KnowledgeScope, KnowledgeStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DemoInstitutionalLearning")


async def run_demo():
    logger.info("==========================================================================")
    logger.info("STARTING PHASE 18 INSTITUTIONAL LEARNING & ORGANIZATIONAL MEMORY DEMO")
    logger.info("==========================================================================")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        repo = SQLAlchemyKnowledgeRepository(session)
        val_svc = KnowledgeValidationService(repo)
        learn_svc = InstitutionalLearningService(repo, val_svc)
        proc_svc = ProcedureManagementService(repo)
        exp_svc = OrganizationalExperimentService(repo, val_svc)
        retrieval_svc = MemoryRetrievalService(memory_repo=None, knowledge_repo=repo)
        context_builder = MemoryContextBuilder(retrieval_service=retrieval_svc)

        # STEP 1: Learn from Task Execution Failure
        logger.info("\n--- 1. LEARNING FROM TASK EXECUTION FAILURE ---")
        item = await learn_svc.learn_from_failure(
            task_id="task-recovery-888",
            failure_description="Async DB connection pool exhausted under peak load",
            recovery_strategy_used="Increased pool_size=20 and max_overflow=10",
        )
        await session.commit()
        logger.info(f"Learned Knowledge Candidate [{item.id}]: '{item.statement}'")
        logger.info(f"Initial Status: {item.status.value}, Authority: {item.authority.value}")

        # STEP 2: Independent Evidence Validation & Anti-Poisoning Check
        logger.info("\n--- 2. INDEPENDENT EVIDENCE VALIDATION & ANTI-POISONING ---")
        # Attempt 2A: Fake LLM output evidence alone -> Rejected
        val_fail = await val_svc.validate_candidate_knowledge(
            knowledge_id=item.id,
            validator_id="agent-eval-1",
            evidence_ids=["llm_gen_output_1", "llm_text_opinion"],
        )
        logger.info(f"LLM Evidence Alone Result: {val_fail.validation_status} - {val_fail.rationale}")

        # Attempt 2B: Deterministic system telemetry/verification log -> Accepted
        val_pass = await val_svc.validate_candidate_knowledge(
            knowledge_id=item.id,
            validator_id="system-verification-engine",
            evidence_ids=["ev_telemetry_logs_2026_09_16"],
        )
        await session.commit()
        logger.info(f"Deterministic Evidence Result: {val_pass.validation_status}")

        validated_item = await repo.get_knowledge_item_by_id(item.id)
        logger.info(f"Promoted Authority: {validated_item.authority.value}, Status: {validated_item.status.value}")

        # STEP 3: Conflict Detection & Resolution
        logger.info("\n--- 3. CONFLICT DETECTION & RESOLUTION ---")
        item_conflicting = await repo.save_knowledge_item(
            KnowledgeItem(
                statement="Async DB connection pool exhausted under load due to sync driver blockage",
                status=KnowledgeStatus.CANDIDATE,
                scope=KnowledgeScope.COMPANY,
            )
        )
        await session.commit()

        conflicts = await val_svc.detect_conflicts_for_item(item_conflicting)
        logger.info(f"Detected {len(conflicts)} knowledge conflict(s)")
        if conflicts:
            conf = conflicts[0]
            resolved = await val_svc.resolve_conflict(
                conflict_id=conf.id,
                resolution_strategy="Keep connection pool scaling policy authoritative",
                winning_knowledge_id=item.id,
            )
            await session.commit()
            logger.info(f"Conflict [{resolved.id}] Status: {resolved.status.value}")

        # STEP 4: Versioned Procedure Management & Governance Approval
        logger.info("\n--- 4. VERSIONED PROCEDURE & GOVERNANCE APPROVAL ---")
        proc = await proc_svc.create_procedure(
            title="Async DB Connection Pool Tuning Procedure",
            purpose="Standard operating procedure for connection pool configuration under high load",
            steps=[
                {"step": 1, "action": "Inspect pool saturation metrics"},
                {"step": 2, "action": "Apply pool_size=20, max_overflow=10 in config"},
            ],
            expected_outcome="Pool saturation drops below 60%",
            scope=KnowledgeScope.COMPANY,
        )
        await session.commit()
        logger.info(f"Created Procedure [{proc.id}]: '{proc.title}' (Version {proc.version}, Governance Approved: {proc.is_governance_approved})")

        approved_proc = await proc_svc.approve_procedure_by_governance(proc.id, "gov-appr-phase11-999")
        await session.commit()
        logger.info(f"Approved Procedure [{approved_proc.id}]: Status={approved_proc.validation_status.value}, Approved={approved_proc.is_governance_approved}")

        # STEP 5: Isolated Organizational Experiment
        logger.info("\n--- 5. ISOLATED ORGANIZATIONAL EXPERIMENT ---")
        exp = await exp_svc.propose_experiment(
            title="Read Replica Offloading Experiment",
            hypothesis="Routing read queries to replica reduces primary pool load by 50%",
            risk_level="HIGH",
            treatment_params={"use_read_replica": True},
        )
        await session.commit()
        logger.info(f"Proposed Experiment [{exp.id}]: Status={exp.status.value}, Risk={exp.risk_level}, Isolated={exp.is_isolated}")

        started_exp = await exp_svc.start_experiment(exp.id, governance_approval_id="gov-exp-appr-777")
        await session.commit()
        logger.info(f"Started Experiment [{started_exp.id}]: Status={started_exp.status.value}")

        completed_exp = await exp_svc.complete_experiment(
            exp.id,
            results={"pool_load_reduction_pct": 52.4},
            conclusion="Read replica routing reduced primary connection pool load by 52.4%.",
        )
        await session.commit()
        logger.info(f"Completed Experiment [{completed_exp.id}]: Conclusion='{completed_exp.conclusion}'")

        exp_candidate = await exp_svc.convert_experiment_to_knowledge_candidate(exp.id)
        await session.commit()
        logger.info(f"Converted Experiment to Knowledge Candidate [{exp_candidate.id}]: '{exp_candidate.statement}'")

        # STEP 6: Knowledge Retrieval & Security Context Framing
        logger.info("\n--- 6. KNOWLEDGE RETRIEVAL & SECURITY FRAMING ---")
        search_results = await retrieval_svc.retrieve_institutional_knowledge(query="DB connection pool")
        logger.info(f"Retrieved {len(search_results)} knowledge items for query 'DB connection pool'")

        context_pkg = await context_builder.build_context(
            task_id="task-recovery-888",
            requesting_employee_id="emp-arch-1",
            query="DB connection pool",
        )
        logger.info("\nFormatted Security Context for Downstream Agent:")
        logger.info("--------------------------------------------------------------------------")
        logger.info(context_pkg["framed_prompt_context"])
        logger.info("--------------------------------------------------------------------------")

    await engine.dispose()
    logger.info("\n==========================================================================")
    logger.info("PHASE 18 INSTITUTIONAL LEARNING E2E DEMO COMPLETED SUCCESSFULLY!")
    logger.info("==========================================================================")


if __name__ == "__main__":
    asyncio.run(run_demo())
