"""
Unit tests for RecoveryEngine (Phase 10).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.application.recovery_engine import RecoveryEngine
from src.domain.recovery import (
    FailureBudget,
    FailureCategory,
    RecoveryStrategy,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.verification_repository import VerificationRepository


@pytest.fixture
def recovery_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    repo = VerificationRepository(session)
    budget = FailureBudget(max_retries=2, max_reworks=2, max_reassignments=1, max_recovery_attempts=4)
    return RecoveryEngine(repository=repo, default_budget=budget)


def test_failure_classification_and_rework(recovery_engine):
    task_id = "task-rework-1"

    failure = recovery_engine.classify_and_record_failure(
        task_id=task_id,
        category=FailureCategory.TEST_FAILURE,
        summary="Pytest exit code 1",
        severity="HIGH",
    )

    assert failure.category == FailureCategory.TEST_FAILURE
    assert failure.recommended_strategy == RecoveryStrategy.REWORK

    # Execute recovery action
    action = recovery_engine.execute_recovery(failure.failure_id)
    assert action.strategy == RecoveryStrategy.REWORK
    assert action.attempt_number == 1
    assert action.success


def test_recovery_loop_exhaustion_escalation(recovery_engine):
    task_id = "task-exhaustion-2"

    # Simulate repeated failures exceeding rework & reassignment limits
    for i in range(1, 6):
        f = recovery_engine.classify_and_record_failure(
            task_id=task_id,
            category=FailureCategory.AGENT_FAILURE,
            summary=f"Failure attempt {i}",
        )
        action = recovery_engine.execute_recovery(f.failure_id)

        if i <= 2:
            assert action.strategy == RecoveryStrategy.REWORK
        elif i == 3:
            assert action.strategy == RecoveryStrategy.REASSIGN
        else:
            assert action.strategy == RecoveryStrategy.ESCALATE
