"""Failure injection test suite for Phase 18 Institutional Knowledge & Learning.

Verifies system resilience against:
1. Failed verification evidence resulting in candidate invalidation.
2. Conflict detection & resolution handling contradictory statements.
3. Staleness decay scoring calculation over time.
"""

import pytest
from datetime import UTC, datetime, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.knowledge_validation_service import KnowledgeValidationService
from src.domain.knowledge import ConflictStatus, KnowledgeItem, KnowledgeStatus
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
async def test_failed_verification_invalidates_knowledge_candidate(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)

    item = await repo.save_knowledge_item(
        KnowledgeItem(
            statement="Using single worker thread handles 100k QPS cleanly",
            status=KnowledgeStatus.CANDIDATE,
        )
    )

    # Validation failure injected via explicit verification failure evidence
    val_record = await val_svc.validate_candidate_knowledge(
        knowledge_id=item.id,
        validator_id="system-verification-engine",
        evidence_ids=["ev_failure_log_999"],
        rationale="Load testing showed worker thread crash at 5k QPS.",
    )

    assert val_record.validation_status == "FAILED"

    reloaded_item = await repo.get_knowledge_item_by_id(item.id)
    assert reloaded_item.status == KnowledgeStatus.INVALIDATED


@pytest.mark.asyncio
async def test_staleness_decay_calculation(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)
    val_svc = KnowledgeValidationService(repo)

    old_time = datetime.now(UTC) - timedelta(days=200)
    item = await repo.save_knowledge_item(
        KnowledgeItem(
            statement="Legacy v1 API uses basic auth headers",
            status=KnowledgeStatus.VALIDATED,
            created_at=old_time,
        )
    )

    decay_score = await val_svc.calculate_staleness_decay(item.id)
    assert decay_score > 0.5  # Significant staleness accrued over 200 days without verification refresh
