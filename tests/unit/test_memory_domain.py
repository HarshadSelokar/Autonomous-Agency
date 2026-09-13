"""
Unit tests for MemoryEntry domain entity, types, scopes, authority levels, and state machine.
"""

from datetime import UTC, datetime
import pytest

from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryProvenance,
    MemoryScope,
    MemoryStateError,
    MemoryStatus,
    MemoryType,
    MemoryValidationError,
)


def test_memory_entry_creation_and_validation() -> None:
    entry = MemoryEntry(
        id="mem-100",
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.TASK,
        owner_id="TASK:t-100",
        content="PostgreSQL supports JSONB and vector embeddings via pgvector.",
        authority=MemoryAuthority.CONFIRMED,
        confidence=0.9,
        provenance=MemoryProvenance.DECISION,
        decision_id="d-100",
    )
    assert entry.id == "mem-100"
    assert entry.memory_type == MemoryType.SEMANTIC
    assert entry.scope == MemoryScope.TASK
    assert entry.authority == MemoryAuthority.CONFIRMED
    assert entry.confidence == 0.9
    assert entry.status == MemoryStatus.ACTIVE


def test_memory_entry_validation_empty_fields() -> None:
    with pytest.raises(MemoryValidationError, match="Memory ID cannot be empty"):
        MemoryEntry(id="", memory_type=MemoryType.WORKING, scope=MemoryScope.RUN, owner_id="RUN:r-1", content="Text")

    with pytest.raises(MemoryValidationError, match="Memory owner_id cannot be empty"):
        MemoryEntry(id="m-1", memory_type=MemoryType.WORKING, scope=MemoryScope.RUN, owner_id="", content="Text")

    with pytest.raises(MemoryValidationError, match="Memory content cannot be empty"):
        MemoryEntry(id="m-1", memory_type=MemoryType.WORKING, scope=MemoryScope.RUN, owner_id="O1", content="   ")

    with pytest.raises(MemoryValidationError, match="confidence must be between 0.0 and 1.0"):
        MemoryEntry(id="m-1", memory_type=MemoryType.WORKING, scope=MemoryScope.RUN, owner_id="O1", content="Text", confidence=1.5)


def test_memory_lifecycle_transitions() -> None:
    entry = MemoryEntry(
        id="mem-200",
        memory_type=MemoryType.EPISODIC,
        scope=MemoryScope.EMPLOYEE,
        owner_id="EMPLOYEE:emp-1",
        content="Initial Observation",
    )
    assert entry.status == MemoryStatus.ACTIVE

    # ACTIVE -> SUPERSEDED
    entry.transition_to(MemoryStatus.SUPERSEDED)
    assert entry.status == MemoryStatus.SUPERSEDED

    # Cannot transition from SUPERSEDED
    with pytest.raises(MemoryStateError, match="Invalid memory transition"):
        entry.transition_to(MemoryStatus.ACTIVE)


def test_memory_archiving_and_unarchiving() -> None:
    entry = MemoryEntry(
        id="mem-300",
        memory_type=MemoryType.ORGANIZATIONAL,
        scope=MemoryScope.COMPANY,
        owner_id="COMPANY",
        content="Old Policy Document",
    )
    entry.transition_to(MemoryStatus.ARCHIVED)
    assert entry.status == MemoryStatus.ARCHIVED

    entry.transition_to(MemoryStatus.ACTIVE)
    assert entry.status == MemoryStatus.ACTIVE
