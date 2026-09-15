"""
Failure-Injection Tests for Phase 10 Verification & Recovery Engine.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.application.recovery_engine import RecoveryEngine
from src.application.verification_engine import VerificationEngine
from src.domain.recovery import FailureBudget, FailureCategory, RecoveryStrategy
from src.domain.verification import (
    EvidenceTrustLevel,
    RuleSeverity,
    VerificationRule,
    VerificationStatus,
    VerificationType,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.verification_repository import VerificationRepository
import src.infrastructure.models  # noqa: F401


@pytest.fixture
def engines():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    repo = VerificationRepository(Session())
    budget = FailureBudget(max_retries=2, max_reworks=2, max_reassignments=1, max_recovery_attempts=4)
    verif = VerificationEngine(repository=repo)
    rec = RecoveryEngine(repository=repo, default_budget=budget)
    return verif, rec


def test_failure_injection_missing_evidence(engines):
    verif, rec = engines
    task_id = "task-fail-inj-1"

    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Tests",
        description="Run pytest",
        target="pytest",
        expected_condition={"exit_code": 0},
    )
    verif.define_expected_outcome(task_id=task_id, description="Missing Evidence", criteria=[], rules=[rule])

    # No evidence added at all
    result = verif.verify_task(task_id=task_id)
    assert result.status == VerificationStatus.FAILED

    action = rec.process_verification_failure(result)
    assert action.strategy == RecoveryStrategy.REWORK


def test_failure_injection_test_failure(engines):
    verif, rec = engines
    task_id = "task-fail-inj-2"

    rule = VerificationRule(
        rule_id="r1",
        rule_type=VerificationType.TEST_VERIFICATION,
        name="Tests",
        description="Run pytest",
        target="pytest",
        expected_condition={"exit_code": 0},
    )
    verif.define_expected_outcome(task_id=task_id, description="Failing Tests", criteria=[], rules=[rule])

    verif.add_evidence(
        source_type="TestRun",
        source_id="tr-1",
        task_id=task_id,
        trust_level=EvidenceTrustLevel.EXECUTED,
        payload={"exit_code": 1, "failed_count": 5},
    )

    result = verif.verify_task(task_id=task_id)
    assert result.status == VerificationStatus.FAILED
    assert result.recommended_recovery == "REWORK"

    action = rec.process_verification_failure(result)
    assert action.strategy == RecoveryStrategy.REWORK


def test_failure_injection_security_policy_failure(engines):
    _, rec = engines
    task_id = "task-fail-inj-sec"

    failure = rec.classify_and_record_failure(
        task_id=task_id,
        category=FailureCategory.SECURITY_FAILURE,
        summary="Unauthorized key access attempt",
        retryable=False,
    )

    action = rec.execute_recovery(failure.failure_id)
    assert action.strategy == RecoveryStrategy.ESCALATE
