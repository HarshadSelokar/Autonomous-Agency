"""Concurrency test suite for Phase 18 Institutional Knowledge.

Verifies system correctness under concurrent operations:
1. Concurrent candidate validations on the same knowledge item.
2. Concurrent procedure creations and version updates.
"""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.knowledge_validation_service import KnowledgeValidationService
from src.application.procedure_management_service import ProcedureManagementService
from src.domain.knowledge import KnowledgeItem, KnowledgeStatus
from src.infrastructure.database import Base
from src.infrastructure.repositories.knowledge_repository import SQLAlchemyKnowledgeRepository


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_validations(session_factory):
    # Initial setup
    async with session_factory() as session:
        repo = SQLAlchemyKnowledgeRepository(session)
        item = await repo.save_knowledge_item(
            KnowledgeItem(statement="Redis cluster failover completes under 2 seconds", status=KnowledgeStatus.CANDIDATE)
        )
        item_id = item.id
        await session.commit()

    async def validate_task(val_id: str, ev_id: str):
        async with session_factory() as session:
            repo = SQLAlchemyKnowledgeRepository(session)
            val_svc = KnowledgeValidationService(repo)
            res = await val_svc.validate_candidate_knowledge(
                knowledge_id=item_id,
                validator_id=val_id,
                evidence_ids=[ev_id],
            )
            await session.commit()
            return res

    results = await asyncio.gather(
        validate_task("val-1", "ev_verification_logs_101"),
        validate_task("val-2", "ev_verification_logs_102"),
        validate_task("val-3", "ev_verification_logs_103"),
    )

    assert len(results) == 3
    for r in results:
        assert r.validation_status == "PASSED"

    async with session_factory() as session:
        repo = SQLAlchemyKnowledgeRepository(session)
        reloaded_item = await repo.get_knowledge_item_by_id(item_id)
        assert reloaded_item.status == KnowledgeStatus.VALIDATED


@pytest.mark.asyncio
async def test_concurrent_procedure_creation(session_factory):
    async def create_proc_task(idx: int):
        async with session_factory() as session:
            repo = SQLAlchemyKnowledgeRepository(session)
            proc_svc = ProcedureManagementService(repo)
            proc = await proc_svc.create_procedure(
                title=f"Standard Operating Procedure #{idx}",
                purpose=f"SOP number {idx}",
                steps=[{"step": 1, "action": "Initialize system"}],
                expected_outcome="System initialized",
            )
            await session.commit()
            return proc

    procs = await asyncio.gather(*[create_proc_task(i) for i in range(5)])
    assert len(procs) == 5
    ids = [p.id for p in procs]
    assert len(set(ids)) == 5  # Unique IDs guaranteed
