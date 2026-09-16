"""Unit tests for Phase 18 Institutional Knowledge domain entities."""

import pytest

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
    KnowledgeValidation,
    RelationshipType,
)


def test_knowledge_item_creation_and_promotion():
    item = KnowledgeItem(
        statement="Verification pass rate increases with automated unit tests",
        knowledge_type=KnowledgeType.LESSON,
        scope=KnowledgeScope.PROJECT,
        scope_id="proj-101",
    )
    assert item.authority == KnowledgeAuthority.UNVERIFIED
    assert item.status == KnowledgeStatus.CANDIDATE

    item.promote_authority(KnowledgeAuthority.VALIDATED)
    assert item.authority == KnowledgeAuthority.VALIDATED
    assert item.status == KnowledgeStatus.VALIDATED

    with pytest.raises(ValueError, match="Cannot demote authority"):
        item.promote_authority(KnowledgeAuthority.OBSERVED)


def test_knowledge_claim_and_provenance():
    claim = KnowledgeClaim(
        knowledge_id="k-1",
        statement="Async DB sessions prevent transaction blocks",
        source_type="TASK_EXECUTION",
        source_id="task-45",
        evidence_ids=["ev-1", "ev-2"],
    )
    assert claim.authority == KnowledgeAuthority.UNVERIFIED
    assert len(claim.evidence_ids) == 2

    provenance = KnowledgeProvenance(
        knowledge_id="k-1",
        task_id="task-45",
        verification_id="verif-99",
    )
    assert provenance.task_id == "task-45"
    assert provenance.verification_id == "verif-99"


def test_knowledge_conflict_and_relationship():
    conflict = KnowledgeConflict(
        knowledge_id_a="k-1",
        knowledge_id_b="k-2",
        conflict_type="CONTRADICTORY_STATEMENT",
        status=ConflictStatus.OPEN,
    )
    assert conflict.status == ConflictStatus.OPEN

    rel = KnowledgeRelationship(
        source_id="k-1",
        target_id="k-2",
        relationship_type=RelationshipType.CONFLICTS_WITH,
    )
    assert rel.relationship_type == RelationshipType.CONFLICTS_WITH


def test_knowledge_procedure():
    procedure = KnowledgeProcedure(
        title="Standard Code Deployment Procedure",
        purpose="Ensure verified deployment to production",
        steps=[{"step": 1, "action": "Run lint and test suite"}],
        scope=KnowledgeScope.COMPANY,
    )
    assert procedure.version == 1
    assert procedure.validation_status == KnowledgeStatus.CANDIDATE
    assert procedure.is_governance_approved is False
