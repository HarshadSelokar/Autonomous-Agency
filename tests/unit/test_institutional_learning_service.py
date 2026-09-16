"""Unit tests for Phase 18 Application Services."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.institutional_learning_service import InstitutionalLearningService
from src.application.knowledge_validation_service import KnowledgeValidationService
from src.application.organizational_experiment_service import OrganizationalExperimentService
from src.application.procedure_management_service import ProcedureManagementService
from src.domain.experiment import ExperimentStatus
from src.domain.knowledge import ConflictStatus, KnowledgeAuthority, KnowledgeItem, KnowledgeStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_knowledge_validation_pipeline_and_independent_evidence(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)
    learn_svc = InstitutionalLearningService(repo, val_svc)

    item = await learn_svc.learn_from_failure(
        task_id="task-999",
        failure_description="Syntax error in module",
        recovery_strategy_used="Automated code patch",
    )

    # 1. Validation attempt with ONLY LLM outputs fails independent evidence check
    val_fail = await val_svc.validate_candidate_knowledge(
        knowledge_id=item.id,
        validator_id="system_val",
        evidence_ids=["llm_gen_out_1", "llm_gen_out_2"],
    )
    assert val_fail.validation_status == "FAILED"
    assert "LLM outputs alone do not count" in val_fail.rationale

    # 2. Validation attempt with deterministic verification evidence succeeds
    val_pass = await val_svc.validate_candidate_knowledge(
        knowledge_id=item.id,
        validator_id="system_val",
        evidence_ids=["ev_verification_logs_101"],
    )
    assert val_pass.validation_status == "PASSED"

    updated_item = await repo.get_knowledge_item_by_id(item.id)
    assert updated_item.authority == KnowledgeAuthority.VALIDATED


@pytest.mark.asyncio
async def test_conflict_detection_and_resolution(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)

    item1 = await repo.save_knowledge_item(
        KnowledgeItem(id="k-c1", statement="Use sync session for DB writes", status=KnowledgeStatus.VALIDATED)
    )
    item2 = await repo.save_knowledge_item(
        KnowledgeItem(id="k-c2", statement="Do NOT use sync session for DB writes", status=KnowledgeStatus.CANDIDATE)
    )

    conflicts = await val_svc.detect_conflicts_for_item(item2)
    assert len(conflicts) >= 1
    conf_id = conflicts[0].id

    resolved_conf = await val_svc.resolve_conflict(
        conflict_id=conf_id,
        resolution_strategy="Keep async session standard",
        winning_knowledge_id="k-c2",
    )
    assert resolved_conf.status == ConflictStatus.RESOLVED

    superseded_item = await repo.get_knowledge_item_by_id("k-c1")
    assert superseded_item.status == KnowledgeStatus.SUPERSEDED


@pytest.mark.asyncio
async def test_procedure_management_and_governance(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    proc_svc = ProcedureManagementService(repo)

    proc = await proc_svc.create_procedure(
        title="Zero Downtime Alembic Migration",
        purpose="Safe DB migrations",
        steps=[{"step": 1, "action": "Run migration script"}],
        expected_outcome="Database updated",
    )
    assert proc.is_governance_approved is False

    approved_proc = await proc_svc.approve_procedure_by_governance(proc.id, "gov-appr-777")
    assert approved_proc.is_governance_approved is True
    assert approved_proc.validation_status == KnowledgeStatus.AUTHORITATIVE


@pytest.mark.asyncio
async def test_organizational_experiment_service(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)
    exp_svc = OrganizationalExperimentService(repo, val_svc)

    exp = await exp_svc.propose_experiment(
        title="Testing 2x Cache Retention Strategy",
        hypothesis="Doubling cache TTL reduces model latency by 20%",
        risk_level="HIGH",
    )
    assert exp.is_isolated is True

    # Starting HIGH risk experiment without governance approval fails
    with pytest.raises(ValueError, match="requires Phase 11 governance approval"):
        await exp_svc.start_experiment(exp.id)

    # Starting with governance approval succeeds
    started_exp = await exp_svc.start_experiment(exp.id, governance_approval_id="gov-appr-888")
    assert started_exp.status == ExperimentStatus.ACTIVE

    completed_exp = await exp_svc.complete_experiment(
        exp.id,
        results={"latency_reduction_pct": 22.0},
        conclusion="Hypothesis confirmed: 2x cache TTL reduces latency by 22%.",
    )
    assert completed_exp.status == ExperimentStatus.COMPLETED

    k_candidate = await exp_svc.convert_experiment_to_knowledge_candidate(exp.id)
    assert k_candidate.status == KnowledgeStatus.CANDIDATE
