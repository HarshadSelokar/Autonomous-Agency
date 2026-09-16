"""Integration tests for Phase 18 Institutional Knowledge Repository."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.domain.experiment import ExperimentStatus, OrganizationalExperiment
from src.domain.knowledge import (
    ConflictStatus,
    KnowledgeAuthority,
    KnowledgeClaim,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeProcedure,
    KnowledgeProvenance,
    KnowledgeRelationship,
    KnowledgeScope,
    KnowledgeStatus,
    KnowledgeType,
    KnowledgeUsageRecord,
    KnowledgeValidation,
    RelationshipType,
)
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
async def test_knowledge_repository_crud(db_session):
    repo = SQLAlchemyKnowledgeRepository(db_session)

    # 1. Knowledge Item
    item = KnowledgeItem(
        id="k-test-1",
        statement="Verification pass rate improves when unit tests cover 90%+ code paths",
        knowledge_type=KnowledgeType.LESSON,
        scope=KnowledgeScope.COMPANY,
    )
    saved_item = await repo.save_knowledge_item(item)
    assert saved_item.id == "k-test-1"

    fetched_item = await repo.get_knowledge_item_by_id("k-test-1")
    assert fetched_item is not None
    assert fetched_item.statement.startswith("Verification pass rate")

    items = await repo.list_knowledge_items(scope="COMPANY")
    assert len(items) == 1

    search_res = await repo.search_knowledge_items("unit tests")
    assert len(search_res) == 1

    # 2. Claims & Provenance
    claim = KnowledgeClaim(
        id="claim-1",
        knowledge_id="k-test-1",
        statement="Async DB session avoids greenlet thread locks",
        source_id="task-99",
    )
    await repo.save_claim(claim)
    claims = await repo.list_claims_for_knowledge("k-test-1")
    assert len(claims) == 1

    prov = KnowledgeProvenance(
        id="prov-1",
        knowledge_id="k-test-1",
        source_id="task-99",
        task_id="task-99",
    )
    await repo.save_provenance(prov)
    provs = await repo.get_provenance_by_knowledge_id("k-test-1")
    assert len(provs) == 1

    # 3. Validations & Conflicts
    val = KnowledgeValidation(
        id="val-1",
        knowledge_id="k-test-1",
        validator_id="system_validator",
        validation_status="PASSED",
    )
    await repo.save_validation(val)
    vals = await repo.list_validations_for_knowledge("k-test-1")
    assert len(vals) == 1

    conflict = KnowledgeConflict(
        id="conf-1",
        knowledge_id_a="k-test-1",
        knowledge_id_b="k-test-2",
        status=ConflictStatus.OPEN,
    )
    await repo.save_conflict(conflict)
    open_conflicts = await repo.list_open_conflicts()
    assert len(open_conflicts) == 1

    # 4. Relationships
    rel = KnowledgeRelationship(
        id="rel-1",
        source_id="k-test-1",
        target_id="k-test-2",
        relationship_type=RelationshipType.LEADS_TO_LESSON,
    )
    await repo.save_relationship(rel)
    rels = await repo.list_relationships_for_entity("k-test-1")
    assert len(rels) == 1

    # 5. Procedures & Experiments
    proc = KnowledgeProcedure(
        id="proc-1",
        title="Zero Downtime Alembic Migration Procedure",
        purpose="Ensure migration backward compatibility",
    )
    await repo.save_procedure(proc)
    procs = await repo.list_procedures()
    assert len(procs) == 1

    exp = OrganizationalExperiment(
        id="exp-1",
        title="Model Routing Quality Weight Tuning",
        hypothesis="Increasing quality weight improves task success by 5%",
        is_isolated=True,
    )
    await repo.save_experiment(exp)
    exps = await repo.list_experiments()
    assert len(exps) == 1
    assert exps[0].is_isolated is True

    # 6. Usage Record
    usage = KnowledgeUsageRecord(
        id="use-1",
        knowledge_id="k-test-1",
        consumer_id="emp-dev-1",
        outcome_status="SUCCESS",
    )
    await repo.save_usage_record(usage)
    usages = await repo.list_usage_records_for_knowledge("k-test-1")
    assert len(usages) == 1
