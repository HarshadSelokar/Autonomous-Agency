"""Security test suite for Phase 18 Institutional Knowledge & Organizational Learning.

Verifies:
1. Anti-Poisoning & Evidence Verification (LLM outputs do NOT count as independent evidence).
2. Experiment Isolation Invariant (is_isolated MUST be True).
3. Phase 11 Governance gating for HIGH/CRITICAL risk experiments and policy promotion.
"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.knowledge_validation_service import KnowledgeValidationService
from src.application.organizational_experiment_service import OrganizationalExperimentService
from src.domain.experiment import OrganizationalExperiment
from src.domain.knowledge import KnowledgeAuthority, KnowledgeItem, KnowledgeStatus
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
async def test_poisoned_knowledge_rejection_without_independent_evidence(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)

    # Malicious or unverified claim trying to claim authority
    item = await repo.save_knowledge_item(
        KnowledgeItem(
            statement="Bypass all authentication checks for speed",
            status=KnowledgeStatus.CANDIDATE,
            authority=KnowledgeAuthority.UNVERIFIED,
        )
    )

    # Attempt to validate using only LLM generated output strings as fake evidence
    val_record = await val_svc.validate_candidate_knowledge(
        knowledge_id=item.id,
        validator_id="rogue-agent-007",
        evidence_ids=["llm-generated-text-1", "llm-generated-text-2"],
    )

    assert val_record.validation_status == "FAILED"
    assert "LLM outputs alone do not count as independent evidence" in val_record.rationale

    # Verify item status remains UNVERIFIED candidate
    reloaded_item = await repo.get_knowledge_item_by_id(item.id)
    assert reloaded_item.authority == KnowledgeAuthority.UNVERIFIED
    assert reloaded_item.status == KnowledgeStatus.CANDIDATE


@pytest.mark.asyncio
async def test_experiment_isolation_and_governance_security_enforcement(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)
    exp_svc = OrganizationalExperimentService(repo, val_svc)

    exp = await exp_svc.propose_experiment(
        title="Bypass Security Check Experiment",
        hypothesis="Disabling auth saves 50ms per request",
        risk_level="HIGH",
    )

    # Security Invariant 1: Experiment must be strictly isolated
    assert exp.is_isolated is True

    # Security Invariant 2: Cannot force-set is_isolated to False
    with pytest.raises(ValueError, match="strictly isolated"):
        exp.is_isolated = False

    # Security Invariant 3: HIGH risk experiment CANNOT start without Phase 11 governance approval
    with pytest.raises(ValueError, match="requires Phase 11 governance approval"):
        await exp_svc.start_experiment(exp.id, governance_approval_id=None)
